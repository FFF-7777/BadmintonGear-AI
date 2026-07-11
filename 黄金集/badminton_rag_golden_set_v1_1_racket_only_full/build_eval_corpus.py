#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_eval_corpus.py
===================
为 Ragas / DeepEval 这类「LLM 裁判」评估框架，构造标准评测语料 eval_corpus.jsonl。

设计原则（不改动后端核心）：
- answer         : 直接复用现有黄金集评测结果 badminton_rag_golden_results_v1_1_qwen.jsonl
                  （即系统真实输出，确定性、可复现）。
- retrieved_contexts : 不依赖后端回传（/api/chat/send 只回传 sources 元数据，不含正文），
                  改为直接 import 项目内部 safe_search 重新跑一遍【确定性检索】，
                  抓回当时喂给 LLM 的真实 chunk 文本。Chroma top_k 检索是确定性的，
                  复现结果与系统当时所用完全一致。
- reference      : 取自黄金集 expected.reference_answer_summary（用于 context_recall / answer_correctness）。

输出字段（每行一个 JSON）：
  id, group, user_query, answer, retrieved_contexts(list[str]), reference, n_contexts

用法：
  python build_eval_corpus.py
"""
import sys
import os
import json
import types
from pathlib import Path
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent

# 向上查找项目根（含 server/services/vector_store.py）
root = HERE
for _ in range(6):
    if (root / "server" / "services" / "vector_store.py").exists():
        break
    root = root.parent
else:
    raise SystemExit(f"找不到项目根(server/services/vector_store.py)，从 {HERE} 起")

SERVER = root / "server"
load_dotenv(str(root / ".env"))
sys.path.insert(0, str(SERVER))

import config  # noqa: E402  (触发 .env 加载)
from services.vector_store import safe_search  # noqa: E402

RAG_TOP_K = config.RAG_TOP_K

# 默认指向「修正黄金集 + qwen3.7-plus 端到端 run」配对语料；
# 如需重建其他组合，改这两行即可（或后续扩展为 CLI 参数）。
GOLDEN = HERE / "badminton_rag_golden_set_v1_1_racket_only_srcfix.jsonl"
RESULTS = HERE / "badminton_rag_golden_results_v1_1_qwen37_srcfix_run.jsonl"
OUT = HERE / "eval_corpus.jsonl"


def load_jsonl(p: Path):
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def to_msg(obj):
    """把 history 里的 dict 转成带 role/content 属性的对象，供 safe_search 读取。"""
    if isinstance(obj, dict):
        return types.SimpleNamespace(
            role=obj.get("role", ""), content=obj.get("content", "")
        )
    return obj


def main():
    if not GOLDEN.exists():
        raise SystemExit(f"缺少黄金集: {GOLDEN}")
    if not RESULTS.exists():
        raise SystemExit(f"缺少评测结果(请先跑 run 脚本): {RESULTS}")

    goldens = load_jsonl(GOLDEN)
    results_by_id = {r["id"]: r for r in load_jsonl(RESULTS)}

    out_rows = []
    empty_ctx = 0
    for g in goldens:
        cid = g["id"]
        res = results_by_id.get(cid, {})
        answer = res.get("answer") or ""
        reference = (g.get("expected") or {}).get("reference_answer_summary") or ""
        history = [to_msg(m) for m in (g.get("history") or [])]

        # 复现确定性检索，抓回真实 chunk 文本
        contexts = []
        try:
            sr = safe_search(g["user_query"], history=history, top_k=RAG_TOP_K)
            docs = getattr(sr, "documents", []) or []
            contexts = [d.page_content for d in docs if getattr(d, "page_content", "")]
        except Exception as e:  # 检索失败不致命，记空上下文并继续
            print(f"  [WARN] {cid} 检索失败: {e}")

        if not contexts:
            empty_ctx += 1

        out_rows.append({
            "id": cid,
            "group": g.get("group", ""),
            "user_query": g["user_query"],
            "answer": answer,
            "retrieved_contexts": contexts,
            "reference": reference,
            "n_contexts": len(contexts),
        })
        print(f"  {cid:8s} group={g.get('group',''):18s} ctx={len(contexts)} ans_chars={len(answer)}")

    with OUT.open("w", encoding="utf-8") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\n已写出: {OUT}")
    print(f"总条数: {len(out_rows)} | 无检索上下文(闲聊/路由类, Ragas/DeepEval 不适用): {empty_ctx}")


if __name__ == "__main__":
    main()
