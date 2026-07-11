#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ragas_eval.py  (ragas 0.4.3 接口)
=====================================
原拟作为确定性黄金集(0.8816)的三角验证之一；但 Ragas 0.4.3 与百炼端点结构性不兼容（generate_with_schema 走 litellm 触发 qwen 不支持的 n=3 多采样 → 400；且 ragas/langchain embedding 方法不匹配），已如实排除于三角验证之外。脚本保留供后续适配，当前不纳入评测结论。

指标（均 0~1，越大越好）：
  - faithfulness       : 答案是否忠于检索到的上下文（不胡说/不臆造）
  - answer_relevancy  : 答案与问题的相关度
  - context_precision  : 检索到的上下文里「相关片段」排得靠前吗
  - context_recall    : 参考答案是否能从检索上下文中找全
  - answer_correctness: 答案与参考答案的整体一致性（语义）
  - llm_context_recall: 基于 LLM 判断上下文对答题的覆盖度

数据来源：
  - answer            : eval_corpus.jsonl（复用系统真实输出，确定性）
  - retrieved_contexts: eval_corpus.jsonl（safe_search 确定性复现的真实 chunk）
  - reference         : eval_corpus.jsonl（黄金集 reference_answer_summary）

裁判 LLM：接阿里云百炼 OpenAI 兼容端点（qwen3.6-flash-2026-04-16，
        与生成模型 qwen3.7-plus 不同以降低自评偏差）。
        注：用 LangchainLLMWrapper(ChatOpenAI, bypass_n=True) 绕开 ragas 的 n=3 采样
        （百炼 qwen 全系不支持 n>1，否则 litellm 重试会构造百炼不认的 contents 字段 → 400）。

用法：
  python ragas_eval.py                 # 全量（过滤掉无检索上下文的闲聊/路由类）
  EVAL_LIMIT=3 python ragas_eval.py  # 冒烟测试，只跑前 3 条验证 API 接线
"""
import os
import sys
import json
import warnings

warnings.filterwarnings("ignore")
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings  # noqa: E402  langchain 版有 embed_query/embed_documents
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    AnswerCorrectness,
    LLMContextRecall,
)

# ---- 裁判 LLM / Embedding：阿里云百炼 OpenAI 兼容端点 ----
BASE_URL = os.getenv("OPENAI_BASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen3.6-flash-2026-04-16")
EMB_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")

# 关键修复：ragas 0.4.3 的 faithfulness/answer_correctness 等指标默认请求 n=3 多采样，
# 百炼 qwen 只返回 1 个 generation → ragas(litellm) 重试时构造百炼不认的 `contents` 字段 → 400。
# 用 LangchainLLMWrapper 包 ChatOpenAI 并 bypass_n=True，强制走「同 prompt 调 n 次 n=1 独立请求」分支，
# 彻底绕开 n 参数（百炼 qwen 全系不支持 n>1）。裁判用 qwen3.6-flash（与生成模型 qwen3.7-plus 不同，降自评偏差）。注：尽管加了 bypass_n 绕开 n 采样，embedding 方法不匹配仍使 Ragas 跑不通，故已排除，详见文件头说明。
flash_llm = ChatOpenAI(
    model=CHAT_MODEL,
    openai_api_key=API_KEY,
    openai_api_base=BASE_URL,
    temperature=0.0,
)
judge_llm = LangchainLLMWrapper(flash_llm, bypass_n=True)
judge_emb = OpenAIEmbeddings(model=EMB_MODEL, openai_api_key=API_KEY, openai_api_base=BASE_URL)

CORPUS = HERE / "eval_corpus.jsonl"
LIMIT = int(os.getenv("EVAL_LIMIT", "0") or 0)


def load_jsonl(p: Path):
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main():
    if not CORPUS.exists():
        raise SystemExit(f"缺少语料: {CORPUS}（请先跑 build_eval_corpus.py）")

    corpus = load_jsonl(CORPUS)
    # 过滤：faithfulness / context_* 类指标必须有检索上下文；无上下文的闲聊/路由类跳过
    usable = [c for c in corpus if (c.get("retrieved_contexts") or [])]
    if LIMIT > 0:
        usable = usable[:LIMIT]
    print(f"语料总条数={len(corpus)} | 含检索上下文(可用)={len(usable)} | 本次跑={len(usable)}")

    metrics = [
        Faithfulness(),
        AnswerRelevancy(),
        ContextPrecision(),
        ContextRecall(),
        AnswerCorrectness(),
        LLMContextRecall(),
    ]
    for m in metrics:  # 显式注入裁判 LLM / embedding（兜底，evaluate 也会注入）
        try:
            m.llm = judge_llm
        except Exception:
            pass
        try:
            m.embeddings = judge_emb
        except Exception:
            pass

    samples = []
    for c in usable:
        samples.append(
            SingleTurnSample(
                user_input=c["user_query"],
                response=c["answer"],
                retrieved_contexts=c["retrieved_contexts"],
                reference=c.get("reference") or "",
            )
        )

    dataset = EvaluationDataset(samples=samples)
    print("Ragas 评估中（LLM 裁判，请稍候）...")
    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=judge_llm,
        embeddings=judge_emb,
        raise_exceptions=False,
    )

    scores = {}
    for m in metrics:
        try:
            scores[m.name] = float(result[m.name])
        except Exception:
            scores[m.name] = None
    report = {
        "framework": "ragas",
        "ragas_version": getattr(__import__("ragas"), "__version__", "?"),
        "judge_model": CHAT_MODEL,
        "judge_endpoint": BASE_URL,
        "n_cases": len(usable),
        "metrics": scores,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    out = HERE / "ragas_scores.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已写出: {out}")


if __name__ == "__main__":
    main()
