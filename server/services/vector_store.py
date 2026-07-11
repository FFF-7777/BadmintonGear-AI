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
from collections import Counter
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Dict, List, Optional, Sequence

import numpy as np
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
    MIN_CHUNK_CHARS,
    MAX_CHUNK_CHARS,
    RAG_TOP_K,
    RAG_CANDIDATE_K,
    RAG_RRF_K,
    RAG_RELEVANCE_THRESHOLD,
    RERANK_ENABLED,
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
    bm25_scores,
    WORD_RE,
    CHINESE_RE,
    normalize_text,
)

logger = logging.getLogger(__name__)

VECTOR_CACHE_NPZ = CHROMA_DIR / "vector_cache.npz"
VECTOR_CACHE_META = CHROMA_DIR / "vector_cache_meta.json"


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

        documents = self._merge_short_chunks(documents)
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

    @staticmethod
    def _merge_short_chunks(documents: List[Document]) -> List[Document]:
        """Merge tiny trailing fragments so vector chunks stay retrievable and less noisy."""
        merged: List[Document] = []
        for document in documents:
            content = (document.page_content or "").strip()
            if not content:
                continue

            current_title = document.metadata.get("section_title")
            previous_title = merged[-1].metadata.get("section_title") if merged else None
            if (
                merged
                and len(content) < MIN_CHUNK_CHARS
                and current_title == previous_title
                and len(merged[-1].page_content) + len(content) + 2 <= MAX_CHUNK_CHARS
            ):
                merged[-1].page_content = f"{merged[-1].page_content.rstrip()}\n\n{content}"
                continue

            document.page_content = content
            merged.append(document)
        return merged

    @staticmethod
    def _load_vector_cache() -> Optional[dict]:
        if not VECTOR_CACHE_NPZ.exists() or not VECTOR_CACHE_META.exists():
            return None
        try:
            data = np.load(VECTOR_CACHE_NPZ, allow_pickle=False)
            meta = json.loads(VECTOR_CACHE_META.read_text(encoding="utf-8"))
            return {
                "ids": [str(item) for item in data["ids"].tolist()],
                "embeddings": data["embeddings"].astype("float32", copy=False),
                "records": meta,
            }
        except Exception as exc:
            logger.warning("本地向量快照读取失败: %s", exc)
            return None

    @staticmethod
    def _save_vector_cache(ids: List[str], embeddings: np.ndarray, records: List[dict]) -> None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            VECTOR_CACHE_NPZ,
            ids=np.array(ids, dtype=str),
            embeddings=embeddings.astype("float32", copy=False),
        )
        VECTOR_CACHE_META.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")

    def _upsert_vector_cache(
        self,
        file_id: int,
        ids: List[str],
        documents: List[Document],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        cache = self._load_vector_cache()
        keep_ids: List[str] = []
        keep_embeddings: List[np.ndarray] = []
        keep_records: List[dict] = []
        if cache:
            for old_id, old_embedding, old_record in zip(
                cache["ids"],
                cache["embeddings"],
                cache["records"],
            ):
                if (old_record.get("metadata") or {}).get("file_id") == file_id:
                    continue
                keep_ids.append(old_id)
                keep_embeddings.append(old_embedding)
                keep_records.append(old_record)

        new_embeddings = [np.array(item, dtype="float32") for item in embeddings]
        keep_ids.extend(ids)
        keep_embeddings.extend(new_embeddings)
        keep_records.extend([
            {
                "page_content": document.page_content,
                "metadata": dict(document.metadata),
            }
            for document in documents
        ])
        if keep_embeddings:
            self._save_vector_cache(keep_ids, np.vstack(keep_embeddings), keep_records)

    def _delete_vector_cache_by_file_id(self, file_id: int) -> None:
        cache = self._load_vector_cache()
        if not cache:
            return
        keep_ids: List[str] = []
        keep_embeddings: List[np.ndarray] = []
        keep_records: List[dict] = []
        for old_id, old_embedding, old_record in zip(
            cache["ids"],
            cache["embeddings"],
            cache["records"],
        ):
            if (old_record.get("metadata") or {}).get("file_id") == file_id:
                continue
            keep_ids.append(old_id)
            keep_embeddings.append(old_embedding)
            keep_records.append(old_record)
        if keep_embeddings:
            self._save_vector_cache(keep_ids, np.vstack(keep_embeddings), keep_records)
        else:
            VECTOR_CACHE_NPZ.unlink(missing_ok=True)
            VECTOR_CACHE_META.unlink(missing_ok=True)

    def _cache_dense_recall(
        self,
        query: str,
        route: str,
        category: Optional[str],
        candidate_k: int,
    ) -> List[RetrievalCandidate]:
        cache = self._load_vector_cache()
        if not cache:
            return []
        query_vector = np.array(self.embeddings.embed_query(query), dtype="float32")
        matrix = cache["embeddings"]
        query_norm = np.linalg.norm(query_vector) or 1.0
        matrix_norms = np.linalg.norm(matrix, axis=1)
        scores = (matrix @ query_vector) / np.maximum(matrix_norms * query_norm, 1e-8)
        ranked = np.argsort(-scores)
        candidates: List[RetrievalCandidate] = []
        for index in ranked:
            record = cache["records"][int(index)]
            metadata = dict(record.get("metadata") or {})
            if category and metadata.get("category") != category:
                continue
            score = float((scores[int(index)] + 1.0) / 2.0)
            candidates.append(self._to_candidate(
                Document(page_content=record.get("page_content", ""), metadata=metadata),
                route,
                score,
            ))
            if len(candidates) >= candidate_k:
                break
        return candidates

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
        texts = [document.page_content for document in documents]
        metadatas = [dict(document.metadata) for document in documents]
        embeddings = self.embeddings.embed_documents(texts)
        # Chroma 单次 upsert 有最大批量限制（~5461），超限报 ValueError。
        # 分批写入：先清旧再逐批 add，失败时已写部分可被下次重写的 upsert 覆盖。
        if existing_ids:
            self.vectorstore.delete(ids=list(existing_ids))
        self._delete_vector_cache_by_file_id(file_id)
        _CHROMA_UPSERT_BATCH = 5000
        for i in range(0, len(documents), _CHROMA_UPSERT_BATCH):
            batch_ids = ids[i : i + _CHROMA_UPSERT_BATCH]
            self.vectorstore._collection.add(
                ids=batch_ids,
                documents=texts[i : i + _CHROMA_UPSERT_BATCH],
                metadatas=metadatas[i : i + _CHROMA_UPSERT_BATCH],
                embeddings=embeddings[i : i + _CHROMA_UPSERT_BATCH],
            )
        self._upsert_vector_cache(file_id, ids, documents, embeddings)
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
        self._delete_vector_cache_by_file_id(file_id)

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
        try:
            results = self.vectorstore.similarity_search(query, **kwargs)

            # 兼容尚未重新入库、没有 category 元数据的旧向量。
            if category and not results:
                results = self.vectorstore.similarity_search(
                    query,
                    k=candidate_k,
                )
        except Exception as exc:
            logger.warning("Chroma dense recall failed, falling back to local vector cache: %s", exc)
            return self._cache_dense_recall(query, route, category, candidate_k)
        return [
            self._to_candidate(document, route, max(0.0, 1.0 - (rank / max(candidate_k, 1))))
            for rank, document in enumerate(results)
        ]

    @staticmethod
    def _keyword_metadata_text(metadata: dict) -> str:
        """构造用于 BM25 的文档元数据文本（与切分入库时的字段对齐）。"""
        return " ".join(
            str(part) for part in [
                metadata.get("section_title", ""),
                metadata.get("file_name", ""),
                metadata.get("brand", ""),
                metadata.get("series", ""),
                " ".join(metadata.get("model_aliases", []) or []),
            ] if part
        )

    @staticmethod
    def _tokenize_counts(text: str) -> "Counter":
        """词频感知分词：与 rag_pipeline.tokenize 同源，但保留重复以计算 tf（BM25 需要）。"""
        normalized = normalize_text(text).lower()
        tokens: list = list(WORD_RE.findall(normalized))
        for segment in CHINESE_RE.findall(normalized):
            tokens.append(segment)
            if len(segment) == 1:
                tokens.append(segment)
            else:
                tokens.extend(segment[i:i + 2] for i in range(len(segment) - 1))
        tokens.extend(t.lower() for t in extract_model_tokens(text))
        return Counter(tokens)

    def _keyword_recall(
        self,
        analysis: QueryAnalysis,
        candidate_k: int,
    ) -> List[RetrievalCandidate]:
        # P1c：按前置分类做 where 预过滤，减少全库拉取与内存扫描；
        # _build_documents 总会写入 category（缺失时回退 "general"），故该过滤安全。
        # 纯读取 chroma（collection.get），不改写入/索引，"知识库向量库不要动"约束下安全。
        get_kwargs: Dict[str, object] = {"include": ["documents", "metadatas"]}
        if analysis.category:
            get_kwargs["where"] = {"category": analysis.category}
        rows = []
        try:
            data = self.vectorstore.get(**get_kwargs)
            source_rows = zip(data.get("documents", []), data.get("metadatas", []))
        except Exception as exc:
            logger.warning("Chroma metadata recall failed, falling back to local vector cache: %s", exc)
            cache = self._load_vector_cache()
            source_rows = [
                (record.get("page_content", ""), record.get("metadata") or {})
                for record in (cache or {}).get("records", [])
            ]

        for content, metadata in source_rows:
            metadata = metadata or {}
            stored_category = metadata.get("category")
            if (
                analysis.category
                and stored_category
                and stored_category != analysis.category
            ):
                continue
            rows.append((content, metadata))

        if not rows:
            return []

        # P1-1：BM25 关键词召回（替代原 token 覆盖率打分，引入 IDF 区分度）。
        # 语料 = 内容 + 元数据文本；IDF 在"类别语料"内计算，无需重索引 chroma。
        corpus = [
            self._tokenize_counts(content + " " + self._keyword_metadata_text(meta))
            for content, meta in rows
        ]
        doc_freq: Dict[str, int] = {}
        for toks in corpus:
            for term in toks:
                doc_freq[term] = doc_freq.get(term, 0) + 1
        doc_lens = [sum(toks.values()) for toks in corpus]

        query_tokens = tokenize(analysis.expanded_query)
        if not query_tokens:
            return []

        raw_scores = bm25_scores(query_tokens, corpus, doc_freq, doc_lens)

        max_score = max(raw_scores)
        candidates = []
        for (content, metadata), raw in zip(rows, raw_scores):
            norm = (raw / max_score) if max_score > 0 else 0.0
            if norm > 0:
                candidates.append(self._to_candidate(
                    Document(page_content=content, metadata=metadata),
                    "keyword",
                    norm,
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


def _chroma_error_note(err: str, data: Optional[dict] = None) -> str:
    """把子进程回传的可捕获异常翻译成对用户/运维友好的原因。

    data 为子进程回传的完整 JSON（可能含 ``hnsw_corrupted`` / ``mode`` 标记），
    用于区分 HNSW 损坏时是否已自动恢复，避免向用户传递误导性文案。
    """
    lowered = err.lower()
    if "OPENAI_API_KEY" in err:
        return "向量检索不可用：OPENAI_API_KEY 未配置或无效（请在项目根 .env 中填写正确的 API Key）。"
    if "401" in err or "authentication" in lowered or "api key" in lowered:
        return "向量检索不可用：向量化服务鉴权失败（OPENAI_API_KEY 无效）。"
    if "timeout" in lowered or "timed out" in lowered:
        return "向量检索不可用：向量化服务响应超时（请检查网络或 OPENAI_BASE_URL）。"
    # HNSW 索引损坏（chroma 1.5.9 Windows 常见问题）
    if any(kw in lowered for kw in ("hnsw", "segment reader", "compactor", "backfill")):
        if data and data.get("hnsw_corrupted"):
            mode = data.get("mode")
            if mode == "search":
                return ("向量库索引损坏（HNSW），检索已降级为空结果（不影响其他接口）。"
                        "请重启后端服务后重新上传知识库文件以重建索引。")
            if mode == "delete":
                return ("向量库索引损坏（HNSW），删除未完成（文件记录已移除）。"
                        "请重启后端服务后重新上传知识库文件以重建索引。")
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
        return _degraded_chroma(_chroma_error_note(err, data), {"chroma": err})
    docs = [
        Document(page_content=d["page_content"], metadata=d.get("metadata", {}))
        for d in data.get("documents", [])
    ]
    # P0-1：Cross-Encoder 语义重排（主进程，隔离于 chroma 子进程）。
    # 仅在开关开启且 rerank 返回有效结果时重排候选顺序；否则保留启发式顺序。
    # rerank 故障（超时/鉴权/网络）只退回启发式，绝不因此丢掉检索结果。
    if docs and RERANK_ENABLED:
        try:
            from services.rerank import rerank as _rerank
            pairs = _rerank(query, [d.page_content for d in docs])
            if pairs:
                score_by_index = {idx: sc for idx, sc in pairs}
                aligned = [score_by_index.get(i, 0.0) for i in range(len(docs))]
                ordered = sorted(zip(aligned, docs), key=lambda item: item[0], reverse=True)
                docs = [doc for _, doc in ordered]
                for score, doc in ordered:
                    doc.metadata["rerank_score"] = round(score, 6)
        except Exception as exc:
            logger.warning("rerank 应用失败，保留启发式排序：%s", exc)
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
        return 0, _chroma_error_note(err, data)
    return data.get("chunk_count", 0), None


def safe_delete_documents(file_id: int, timeout: int = 40) -> Optional[str]:
    """隔离式删除：返回 None 表示成功，返回字符串表示错误原因（子进程崩溃/异常）。
    直接调用 Chroma 删除可能触发原生崩溃，必须走子进程隔离（修复删除接口遗漏的隔离缺口）。"""
    payload = {"mode": "delete", "file_id": file_id}
    data = _run_chroma_subprocess(payload, timeout=timeout)
    if not data:
        return "vector store subprocess crashed (chroma env incompatible)"
    err = data.get("_error") if isinstance(data, dict) else None
    return _chroma_error_note(err, data)
