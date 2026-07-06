"""
Chroma向量数据库服务
负责文档向量化存储，以及多路召回、RRF融合和精排
"""
import hashlib
import json
import logging
import subprocess
import sys as _sys
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Dict, List, Optional, Sequence

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


from config import (
    BASE_DIR,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
    CHROMA_DIR,
    CHROMA_COLLECTION,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    RAG_TOP_K,
    RAG_CANDIDATE_K,
    RAG_RRF_K,
    RAG_RELEVANCE_THRESHOLD,
)
from services.rag_pipeline import (
    QueryAnalysis,
    RetrievalCandidate,
    analyze_query,
    infer_category,
    reciprocal_rank_fusion,
    rerank_candidates,
    split_knowledge_sections,
    tokenize,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RAGSearchResult:
    """一次完整检索的结果与可观察信息。"""

    analysis: QueryAnalysis
    documents: List[Document]
    route_counts: Dict[str, int]
    route_errors: Dict[str, str]


class VectorStoreService:
    """Chroma向量数据库服务类"""

    def __init__(self):
        """初始化嵌入模型和向量存储"""
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_BASE_URL,
            dimensions=EMBEDDING_DIMENSIONS,
            # 阿里云兼容接口只接受 str / list[str]，LangChain 默认会发送 token id 数组导致 400
            check_embedding_ctx_length=False,
            # 阿里云 text-embedding-v4 限制单次批量 <=10 条，超限返回 400；分批嵌入规避限制
            chunk_size=10,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        self._vectorstore: Optional[Chroma] = None

    @property
    def vectorstore(self) -> Chroma:
        """
        获取或创建Chroma向量存储实例
        :return: Chroma向量存储
        """
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name=CHROMA_COLLECTION,
                embedding_function=self.embeddings,
                persist_directory=str(CHROMA_DIR),
            )
        return self._vectorstore

    def _build_documents(
        self,
        text: str,
        file_id: int,
        file_name: str,
        file_type: str,
    ) -> List[Document]:
        """FAQ优先按单问答切分，普通长文回退到递归字符切分。"""
        sections = split_knowledge_sections(text)
        documents: List[Document] = []
        if sections:
            for section in sections:
                section_doc = Document(page_content=section.content)
                section_chunks = self.text_splitter.split_documents([section_doc])
                for chunk in section_chunks:
                    chunk.metadata["section_title"] = section.title
                    documents.append(chunk)
        else:
            documents = self.text_splitter.split_documents([Document(page_content=text)])

        fallback_category = infer_category(file_name) or "general"
        for index, document in enumerate(documents):
            section_title = str(document.metadata.get("section_title", "")).strip()
            category = infer_category(f"{section_title} {document.page_content}") or fallback_category
            chunk_hash = hashlib.sha256(document.page_content.encode("utf-8")).hexdigest()[:16]
            document.metadata.update({
                "file_id": file_id,
                "file_name": file_name,
                "file_type": file_type,
                "category": category,
                "section_title": section_title,
                "chunk_index": index,
                "chunk_id": f"{file_id}:{index}:{chunk_hash}",
            })
        return documents

    def add_documents(
        self,
        text: str,
        file_id: int,
        file_name: str,
        file_type: str,
    ) -> int:
        """
        将文本分块并向量化存入Chroma
        :param text: 文档文本内容
        :param file_id: 知识库文件ID
        :param file_name: 文件名
        :param file_type: 文件类型
        :return: 分块数量
        """
        if not text or not text.strip():
            raise ValueError("文件未解析出有效文本")

        documents = self._build_documents(text, file_id, file_name, file_type)
        if not documents:
            raise ValueError("文件未生成有效知识分块")

        existing = self.vectorstore.get(
            where={"file_id": file_id},
            include=["metadatas"],
        )
        existing_ids = set(existing.get("ids", []))
        ids = [document.metadata["chunk_id"] for document in documents]
        # Chroma 的 upsert 成功后再清理旧块，重新向量化失败时仍保留上一版可用索引。
        self.vectorstore.add_documents(documents, ids=ids)
        stale_ids = list(existing_ids - set(ids))
        if stale_ids:
            self.vectorstore.delete(ids=stale_ids)
        return len(documents)

    def delete_by_file_id(self, file_id: int) -> None:
        """
        根据文件ID删除向量数据
        :param file_id: 知识库文件ID
        """
        existing = self.vectorstore.get(
            where={"file_id": file_id},
            include=["metadatas"],
        )
        ids = existing.get("ids", [])
        if ids:
            self.vectorstore.delete(ids=ids)

    @staticmethod
    def _to_candidate(document: Document, route: str, score: float) -> RetrievalCandidate:
        return RetrievalCandidate(
            content=document.page_content,
            metadata=dict(document.metadata),
            route=route,
            score=score,
        )

    def _dense_recall(
        self,
        query: str,
        route: str,
        category: Optional[str],
        candidate_k: int,
    ) -> List[RetrievalCandidate]:
        kwargs = {"k": candidate_k}
        if category:
            kwargs["filter"] = {"category": category}
        results = self.vectorstore.similarity_search_with_relevance_scores(query, **kwargs)

        # 兼容尚未重新入库、没有 category 元数据的旧向量。
        if category and not results:
            results = self.vectorstore.similarity_search_with_relevance_scores(
                query,
                k=candidate_k,
            )
        return [
            self._to_candidate(document, route, score)
            for document, score in results
        ]

    def _keyword_recall(
        self,
        analysis: QueryAnalysis,
        candidate_k: int,
    ) -> List[RetrievalCandidate]:
        data = self.vectorstore.get(include=["documents", "metadatas"])
        query_tokens = tokenize(analysis.expanded_query)
        candidates = []
        for content, metadata in zip(
            data.get("documents", []),
            data.get("metadatas", []),
        ):
            metadata = metadata or {}
            stored_category = metadata.get("category")
            if (
                analysis.category
                and stored_category
                and stored_category != analysis.category
            ):
                continue

            document_tokens = tokenize(content)
            if not query_tokens:
                continue
            coverage = len(query_tokens & document_tokens) / len(query_tokens)
            title_tokens = tokenize(str(metadata.get("section_title", "")))
            title_coverage = len(query_tokens & title_tokens) / len(query_tokens)
            score = min(1.0, coverage * 0.8 + title_coverage * 0.2)
            if score > 0:
                candidates.append(self._to_candidate(
                    Document(page_content=content, metadata=metadata),
                    "keyword",
                    score,
                ))

        return sorted(candidates, key=lambda item: item.score, reverse=True)[:candidate_k]

    def search(
        self,
        query: str,
        history: Optional[Sequence] = None,
        top_k: int = RAG_TOP_K,
    ) -> RAGSearchResult:
        """
        完整六阶段检索：Query分析、前置过滤、多路召回、去重、RRF、精排。
        :param query: 查询文本
        :param history: 最近会话消息
        :param top_k: 精排后返回数量
        """
        analysis = analyze_query(query, history)
        routes: List[List[RetrievalCandidate]] = []
        route_counts: Dict[str, int] = {}
        route_errors: Dict[str, str] = {}

        try:
            original_route = self._dense_recall(
                analysis.queries[0],
                "dense_original",
                analysis.category,
                RAG_CANDIDATE_K,
            )
        except Exception as exc:
            logger.exception("原始问题向量召回失败")
            route_errors["dense_original"] = str(exc)[:500]
            original_route = []
        routes.append(original_route)
        route_counts["dense_original"] = len(original_route)

        if len(analysis.queries) > 1:
            try:
                enhanced_route = self._dense_recall(
                    analysis.queries[1],
                    "dense_enhanced",
                    analysis.category,
                    RAG_CANDIDATE_K,
                )
            except Exception as exc:
                logger.exception("增强问题向量召回失败")
                route_errors["dense_enhanced"] = str(exc)[:500]
                enhanced_route = []
            routes.append(enhanced_route)
            route_counts["dense_enhanced"] = len(enhanced_route)
        else:
            route_counts["dense_enhanced"] = 0

        keyword_route = self._keyword_recall(analysis, RAG_CANDIDATE_K)
        routes.append(keyword_route)
        route_counts["keyword"] = len(keyword_route)

        fused = reciprocal_rank_fusion(routes, rrf_k=RAG_RRF_K)
        ranked = rerank_candidates(
            analysis,
            fused,
            top_k=top_k,
            threshold=RAG_RELEVANCE_THRESHOLD,
        )

        documents = []
        for candidate in ranked:
            metadata = dict(candidate.metadata)
            metadata.update({
                "retrieval_routes": ",".join(candidate.routes),
                "retrieval_score": round(candidate.final_score, 6),
                "relevance_score": round(candidate.confidence, 6),
            })
            documents.append(Document(
                page_content=candidate.content,
                metadata=metadata,
            ))

        return RAGSearchResult(
            analysis=analysis,
            documents=documents,
            route_counts=route_counts,
            route_errors=route_errors,
        )

    def similarity_search(self, query: str, top_k: int = RAG_TOP_K) -> List[Document]:
        """兼容旧调用方，内部统一走完整检索管线。"""
        return self.search(query, top_k=top_k).documents


# 全局单例
vector_store_service = VectorStoreService()


# ---------------------------------------------------------------------------
# 子进程隔离的稳健封装
# ---------------------------------------------------------------------------
# chroma 1.5.9 的 Rust 绑定在部分 Windows 环境下对 HNSW 索引读写会原生崩溃(segfault)，
# 该异常无法被 Python try/except 捕获，会直接拖死 uvicorn 进程。下面两个函数把实际
# 的 Chroma 操作放到独立子进程(services/chroma_runner.py)中执行：子进程崩溃只影响自身，
# 主进程据此返回空结果/失败，保证服务整体可用、AI 客服可优雅降级。
def _run_chroma_subprocess(payload: dict, timeout: int = 40) -> Optional[dict]:
    """在子进程中执行 Chroma 操作；返回解析后的 JSON dict，失败返回 None。"""
    try:
        proc = subprocess.run(
            [_sys.executable, "-m", "services.chroma_runner"],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(BASE_DIR),
            encoding="utf-8",
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except Exception:
        return None


def safe_search(
    query: str,
    history: Optional[Sequence] = None,
    top_k: int = RAG_TOP_K,
    timeout: int = 40,
) -> SimpleNamespace:
    """隔离式检索：子进程崩溃时返回空文档，不影响主进程。"""
    payload = {
        "mode": "search",
        "query": query,
        "history": [
            {"role": getattr(m, "role", ""), "content": getattr(m, "content", "")}
            for m in (history or [])
        ],
        "top_k": top_k,
    }
    data = _run_chroma_subprocess(payload, timeout=timeout)
    if not data:
        return SimpleNamespace(
            documents=[],
            route_counts={},
            route_errors={"chroma": "vector store unavailable (subprocess crashed)"},
            analysis=None,
        )
    docs = [
        Document(page_content=d["page_content"], metadata=d.get("metadata", {}))
        for d in data.get("documents", [])
    ]
    analysis = data.get("analysis")
    return SimpleNamespace(
        documents=docs,
        route_counts=data.get("route_counts", {}),
        route_errors=data.get("route_errors", {}),
        analysis=analysis,
    )


def safe_add_documents(
    text: str,
    file_id: int,
    file_name: str,
    file_type: str,
    timeout: int = 120,
) -> tuple:
    """隔离式入库：返回 (chunk_count, error_msg)。子进程崩溃时 chunk_count=0。"""
    payload = {
        "mode": "add",
        "text": text,
        "file_id": file_id,
        "file_name": file_name,
        "file_type": file_type,
    }
    data = _run_chroma_subprocess(payload, timeout=timeout)
    if not data:
        return 0, "vector store subprocess crashed (chroma env incompatible)"
    return data.get("chunk_count", 0), None

