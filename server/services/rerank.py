"""
Cross-Encoder 语义重排（P0-1）。

复用 DashScope 的 qwen3-rerank（gte-rerank 已于 2026-05-30 下线）对
"查询 × 已召回候选文档" 做语义相关性二次排序，叠加在现有启发式六维精排之上，
进一步提升 RAG 检索精度（尤其当初始召回 20-100 个相关度参差不齐的候选时）。

设计要点（与"知识库向量库不要动 / 隔离失败域"约束一致）：
- 只在主进程调用（vector_store.safe_search 内），不在 chroma 子进程内，
  避免重排接口故障连累向量检索整体降级为空结果。
- 任意异常 / 非 200 / 超时都返回 None，由调用方退回启发式排序（优雅降级）。
- 无新第三方依赖：直接用标准库 urllib 调 DashScope 原生 rerank 端点。
"""
import json
import logging
import ssl
import urllib.request
from typing import List, Optional, Tuple

from config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    RERANK_BASE_URL,
    RERANK_ENABLED,
    RERANK_MODEL,
    RERANK_TIMEOUT,
)

logger = logging.getLogger(__name__)


def _build_url() -> str:
    """推导原生 rerank 端点。

    优先用显式 RERANK_BASE_URL；否则从 OpenAI 兼容地址推导：
      .../compatible-mode/v1  ->  .../api/v1/services/rerank/text-rerank/text-rerank
    """
    if RERANK_BASE_URL:
        return RERANK_BASE_URL
    host = OPENAI_BASE_URL.split("/compatible-mode")[0]
    return host + "/api/v1/services/rerank/text-rerank/text-rerank"


def rerank(
    query: str,
    documents: List[str],
    top_n: Optional[int] = None,
) -> Optional[List[Tuple[int, float]]]:
    """对 (query, documents) 做语义重排。

    返回与输入 documents 等长、按相关性降序的 [(index, score), ...]，
    index 为输入文档下标。任意失败返回 None（调用方应退回启发式排序）。
    """
    if not RERANK_ENABLED or not OPENAI_API_KEY:
        return None
    if not documents:
        return None

    url = _build_url()
    payload = {
        "model": RERANK_MODEL,
        "input": {
            "query": query,
            "documents": documents,
        },
        "parameters": {"return_documents": False},
    }
    if top_n is not None:
        payload["parameters"]["top_n"] = top_n

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request, timeout=RERANK_TIMEOUT, context=ssl.create_default_context()
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
        results = body.get("output", {}).get("results")
        if not results:
            return None
        return [(int(item["index"]), float(item["relevance_score"])) for item in results]
    except Exception as exc:  # 超时/网络/JSON/鉴权失败一律降级
        logger.warning("rerank 调用失败，退回启发式排序：%s", exc)
        return None
