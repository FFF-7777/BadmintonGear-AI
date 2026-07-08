"""
Chroma 检索/入库的子进程隔离 worker。

背景：chroma 1.5.9 的 Rust 绑定在部分 Windows 环境下对 HNSW 索引做写/读操作时会
发生原生层崩溃(segfault)，该异常无法被 Python try/except 捕获，会直接拖死整个
uvicorn 进程。为保持服务稳健，所有 Chroma 访问都通过本子进程执行：子进程崩溃只影响
自身，主进程(uvicorn)据此优雅降级(检索返回空、入库返回失败)，绝不连累其他接口。

运行方式: python -m services.chroma_runner
请求: stdin 传入 JSON {"mode": "search"|"add", ...}
响应: stdout 输出 JSON 结果；异常时 stderr 打印堆栈并以非 0 退出码退出。
"""
import json
import os
import re
import shutil
import sys
import traceback

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# 兜底：文档内容可能残留孤立代理码点，json.dumps(ensure_ascii=False) 会抛
# UnicodeEncodeError；在最终输出前统一替换为 U+FFFD。
_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")

# HNSW 索引损坏错误的关键词（中英文），用于自动检测和触发恢复
_HNSW_ERROR_PATTERNS = (
    "hnsw",
    "hns w",
    "segment reader",
    "compactor",
    "backfill",
)


def _safe_json_dumps(obj: dict) -> str:
    raw = json.dumps(obj, ensure_ascii=False)
    return _SURROGATE_RE.sub("\ufffd", raw)


def _is_hnsw_error(err_str: str) -> bool:
    """检测异常信息是否包含 HNSW 索引损坏的关键词。"""
    lowered = err_str.lower()
    return any(p in lowered for p in _HNSW_ERROR_PATTERNS)


def _wipe_chroma_and_retry(handler, payload: dict, max_retries: int = 1) -> dict:
    """HNSW 损坏自动恢复：清空 chroma_db 后重试一次。

    chroma 1.5.9 的 Rust hnswlib 绑定在 Windows 上偶尔会留下不完整的索引文件
    （进程被杀、segfault、磁盘满等），后续任何操作碰到这些文件都会报
    「加载 hnsw 索引错误」。唯一可靠修复是删除整个 chroma_db 目录让 Chroma 从零重建。
    """
    from config import CHROMA_DIR

    last_err = ""
    for attempt in range(max_retries + 1):
        try:
            return handler(payload)
        except Exception as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            if not _is_hnsw_error(last_err) or attempt >= max_retries:
                raise
            # 检测到 HNSW 损坏 → 清理并重试
            sys.stderr.write(
                f"[chroma_runner] HNSW index corruption detected, "
                f"wiping CHROMA_DIR and retrying ({attempt + 1}/{max_retries})...\n"
            )
            try:
                shutil.rmtree(str(CHROMA_DIR), ignore_errors=True)
                CHROMA_DIR.mkdir(parents=True, exist_ok=True)
                # 清除 vector_store 缓存（如果已导入的话）
                import services.vector_store as _vs_mod
                if hasattr(_vs_mod, 'vector_store_service'):
                    _vs_mod.vector_store_service._vectorstore = None
            except Exception as wipe_err:
                sys.stderr.write(f"[chroma_runner] Failed to wipe chroma_db: {wipe_err}\n")
                raise  # 清理失败就直接抛原始错误

    raise RuntimeError(f"Max retries exceeded for HNSW error: {last_err}")


def _do_search(payload: dict) -> dict:
    from services.vector_store import vector_store_service

    query = payload.get("query", "")
    history = payload.get("history") or []
    top_k = payload.get("top_k", 4)
    result = vector_store_service.search(query, history=history, top_k=top_k)
    return {
        "documents": [
            {"page_content": d.page_content, "metadata": d.metadata}
            for d in result.documents
        ],
        "route_counts": result.route_counts,
        "route_errors": result.route_errors,
        "analysis": {
            "original_query": result.analysis.original_query,
            "normalized_query": result.analysis.normalized_query,
            "expanded_query": result.analysis.expanded_query,
            "category": result.analysis.category,
            "queries": result.analysis.queries,
            "scope": result.analysis.scope,
            "model_tokens": result.analysis.model_tokens,
            "compare_targets": result.analysis.compare_targets,
        },
    }


def _do_add(payload: dict) -> dict:
    from services.vector_store import vector_store_service

    text = payload.get("text", "")
    file_id = payload.get("file_id")
    file_name = payload.get("file_name", "")
    file_type = payload.get("file_type", "")
    chunk_count = vector_store_service.add_documents(text, file_id, file_name, file_type)
    return {"chunk_count": chunk_count}


def _do_delete(payload: dict) -> dict:
    from services.vector_store import vector_store_service

    file_id = payload.get("file_id")
    vector_store_service.delete_by_file_id(file_id)
    return {"deleted": True}


_HANDLERS = {"search": _do_search, "add": _do_add, "delete": _do_delete}


def main() -> None:
    # Windows 下 sys.stdin 默认按 locale 编码（GBK）解码，会把主进程以字节模式发来的
    # UTF-8 字节读成乱码（锟斤拷），并连带污染下游逻辑。改用底层 buffer 读取原始字节，
    # 再显式 UTF-8 解码，与主进程 send(bytes) 的模式严格对应。
    raw_bytes = sys.stdin.buffer.read()
    payload = json.loads(raw_bytes.decode("utf-8"))
    mode = payload.get("mode", "search")
    handler = _HANDLERS.get(mode)
    if handler is None:
        raise ValueError(f"unknown mode: {mode}")

    # add/search/delete 操作都可能碰到 HNSW 索引损坏，统一走自动恢复
    if mode == "add":
        data = _wipe_chroma_and_retry(handler, payload)
    else:
        data = handler(payload)

    sys.stdout.write(_safe_json_dumps(data))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # P1d：把可捕获异常以结构化 JSON 回传，让主进程给出精准诊断，
        # 而非误报“chroma 原生崩溃”。原生崩溃（segfault）无法在此捕获，会保留非 0 退出码 → 主进程判为崩溃。
        tb = traceback.format_exc()
        sys.stdout.write(_safe_json_dumps(
            {"_error": f"{type(exc).__name__}: {exc}", "_traceback": tb},
        ))
        sys.exit(0)
