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
import sys
import json
import traceback

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


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


_HANDLERS = {"search": _do_search, "add": _do_add}


def main() -> None:
    payload = json.load(sys.stdin)
    mode = payload.get("mode", "search")
    handler = _HANDLERS.get(mode)
    if handler is None:
        raise ValueError(f"unknown mode: {mode}")
    data = handler(payload)
    sys.stdout.write(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
