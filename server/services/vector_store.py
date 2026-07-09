"""
Chroma向量数据库服务
负责文档向量化存储，以及多路召回、RRF融合和精排
"""
import hashlib
import json
import logging
import re
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
    extract_model_tokens,
    infer_category,
    infer_brand,
    infer_doc_type,
    infer_series,
    model_alias_variants,
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
        """初始化轻量对象；外部 API 客户端按需创建。"""
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        self._vectorstore: Optional[Chroma] = None

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY 未配置，知识库向量化与向量检索不可用")
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                openai_api_key=OPENAI_API_KEY,
                openai_api_base=OPENAI_BASE_URL,
                dimensions=EMBEDDING_DIMENSIONS,
                # 阿里云兼容接口只接受 str / list[str]，LangChain 默认会发送 token id 数组导致 400
                check_embedding_ctx_length=False,
                # 阿里云 text-embedding-v4 限制单次批量 <=10 条，超限返回 400；分批嵌入规避限制
                chunk_size=10,
            )
        return self._embeddings

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
        # 防御性清理：上游文件解析可能残留孤立代理码点（lone surrogate），
        # 会导致后续 .encode("utf-8") / json.dumps 炸 UnicodeEncodeError。
        _SURROGATE_RE = re.compile(r"[\ud800-\udfff]")
        text = _SURROGATE_RE.sub("\ufffd", text) if text else text

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
            context_text = f"{file_name} {section_title} {document.page_content}"
            category = infer_category(context_text) or fallback_category
            model_tokens = extract_model_tokens(context_text)
            model_aliases: List[str] = []
            for token in model_tokens:
                model_aliases.extend(model_alias_variants(token))
            chunk_hash = hashlib.sha256(document.page_content.encode("utf-8")).hexdigest()[:16]
            meta: dict = {
                "file_id": file_id,
                "file_name": file_name,
                "file_type": file_type,
                "category": category,
                "section_title": section_title,
                "chunk_index": index,
                "chunk_id": f"{file_id}:{index}:{chunk_hash}",
                "brand": infer_brand(context_text) or "",
                "series": infer_series(context_text) or "",
                "doc_type": infer_doc_type(context_text),
            }
            # Chroma upsert 要求所有 metadata 值必须非空；型号术语类 chunk
            # 可能不含任何型号名（如规则/术语文档），此时 model_tokens/model_aliases
            # 为空列表 → 触发 ValueError。仅当非空时才写入。
            if model_tokens:
                meta["model_tokens"] = list(dict.fromkeys(model_tokens))
            if model_aliases:
                meta["model_aliases"] = list(dict.fromkeys(model_aliases))
            document.metadata.update(meta)
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
        # Chroma 单次 upsert 有最大批量限制（~5461），超限报 ValueError。
        # 分批写入：先清旧再逐批 add，失败时已写部分可被下次重写的 upsert 覆盖。
        self.vectorstore.delete(ids=list(existing_ids))
        _CHROMA_UPSERT_BATCH = 5000
        for i in range(0, len(documents), _CHROMA_UPSERT_BATCH):
            batch_docs = documents[i : i + _CHROMA_UPSERT_BATCH]
            batch_ids = ids[i : i + _CHROMA_UPSERT_BATCH]
            self.vectorstore.add_documents(batch_docs, ids=batch_ids)
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
        # P1c：按前置分类做 where 预过滤，减少全库拉取与内存扫描；
        # _build_documents 总会写入 category（缺失时回退 "general"），故该过滤安全。
        get_kwargs: Dict[str, object] = {"include": ["documents", "metadatas"]}
        if analysis.category:
            get_kwargs["where"] = {"category": analysis.category}
        data = self.vectorstore.get(**get_kwargs)
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
            metadata_text = " ".join(
                str(part) for part in [
                    metadata.get("section_title", ""),
                    metadata.get("file_name", ""),
                    metadata.get("brand", ""),
                    metadata.get("series", ""),
                    " ".join(metadata.get("model_aliases", []) or []),
                ] if part
            )
            metadata_tokens = tokenize(metadata_text)
            coverage = len(query_tokens & (document_tokens | metadata_tokens)) / len(query_tokens)
            title_tokens = tokenize(str(metadata.get("section_title", "")))
            title_coverage = len(query_tokens & title_tokens) / len(query_tokens)
            metadata_coverage = len(query_tokens & metadata_tokens) / len(query_tokens) if metadata_tokens else 0.0
            score = min(1.0, coverage * 0.65 + title_coverage * 0.15 + metadata_coverage * 0.20)
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
    """在子进程中执行 Chroma 操作。

    - 成功：返回解析后的 JSON dict（可能含 _error 字段表示子进程内可捕获异常）。
    - 原生崩溃（segfault，exit!=0）或解析失败：返回 None。
    主进程据此区分"可诊断的业务错误"与"真正的崩溃"，给出精准提示。

    Windows 兼容：使用纯字节模式（input=bytes, 不用 text=True），避免 Windows 管道
    在 text=True 时将 UTF-8 中文按系统默认编码（GBK/GB2312）二次解码导致
    "锟斤拷"乱码，并连带污染 API Key 等字段导致 401 鉴权失败。
    """
    try:
        proc = subprocess.run(
            [_sys.executable, "-m", "services.chroma_runner"],
            input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            capture_output=True,
            timeout=timeout,
            cwd=str(BASE_DIR),
        )
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None
    if proc.returncode != 0:
        # 真正的原生崩溃（如 chroma Rust 绑定 segfault），无法被 Python 捕获
        return None
    try:
        return json.loads(proc.stdout.decode("utf-8", errors="replace"))
    except Exception:
        return None


# 向量检索不可用时的文案（按真实根因生成，避免误导）
_CHROMA_CRASH_NOTE = (
    "向量检索不可用：向量库子进程异常退出（疑似 chroma 原生崩溃），已隔离，不影响其他接口。"
)


def _chroma_error_note(err: str) -> str:
    """把子进程回传的可捕获异常翻译成对用户/运维友好的原因。"""
    lowered = err.lower()
    if "OPENAI_API_KEY" in err:
        return "向量检索不可用：OPENAI_API_KEY 未配置或无效（请在项目根 .env 中填写正确的 API Key）。"
    if "401" in err or "authentication" in lowered or "api key" in lowered:
        return "向量检索不可用：向量化服务鉴权失败（OPENAI_API_KEY 无效）。"
    if "timeout" in lowered or "timed out" in lowered:
        return "向量检索不可用：向量化服务响应超时（请检查网络或 OPENAI_BASE_URL）。"
    # HNSW 索引损坏（chroma 1.5.9 Windows 常见问题）
    if any(kw in lowered for kw in ("hnsw", "segment reader", "compactor", "backfill")):
        return ("向量库索引损坏（HNSW），已自动清理并重试。如果仍失败，"
                "请重启后端服务后重新上传知识库文件。")
    return f"向量检索不可用：{err}"


def _degraded_chroma(note: str, route_errors: dict) -> SimpleNamespace:
    return SimpleNamespace(
        documents=[],
        route_counts={},
        route_errors=route_errors,
        analysis=None,
        note=note,
    )


def safe_search(
    query: str,
    history: Optional[Sequence] = None,
    top_k: int = RAG_TOP_K,
    timeout: int = 40,
) -> SimpleNamespace:
    """隔离式检索：子进程崩溃或异常时返回空文档与真实原因，不影响主进程。"""
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
        return _degraded_chroma(_CHROMA_CRASH_NOTE, {"chroma": "vector store subprocess crashed (native)"})
    err = data.get("_error") if isinstance(data, dict) else None
    if err:
        return _degraded_chroma(_chroma_error_note(err), {"chroma": err})
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
    timeout: int = 600,
) -> tuple:
    """隔离式入库：返回 (chunk_count, error_msg)。子进程崩溃或异常都返回错误原因。"""
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
    err = data.get("_error") if isinstance(data, dict) else None
    if err:
        return 0, err
    return data.get("chunk_count", 0), None


def safe_delete_documents(file_id: int, timeout: int = 40) -> Optional[str]:
    """隔离式删除：返回 None 表示成功，返回字符串表示错误原因（子进程崩溃/异常）。
    直接调用 Chroma 删除可能触发原生崩溃，必须走子进程隔离（修复删除接口遗漏的隔离缺口）。"""
    payload = {"mode": "delete", "file_id": file_id}
    data = _run_chroma_subprocess(payload, timeout=timeout)
    if not data:
        return "vector store subprocess crashed (chroma env incompatible)"
    err = data.get("_error") if isinstance(data, dict) else None
    return err
