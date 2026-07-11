#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deepeval_eval.py  (deepeval 4.0.8 接口)
=========================================
用 DeepEval 对羽智选 RAG 系统做【独立 LLM 裁判】评估，作为确定性黄金集(0.863)的三角验证之二。

指标（0~1，越大越好；阈值 0.5 即"通过"）：
  - faithfulness       : 答案是否忠于检索上下文（不臆造）
  - answer_relevancy  : 答案与问题相关度
  - contextual_precision: 检索上下文里相关片段靠前程度
  - contextual_recall  : 参考答案能否从检索上下文覆盖
  - hallucination      : 幻觉程度（1=无幻觉）
  - GEval(专业度)     : 用 G-Eval 把"羽球装备专业度"当裁判标准打分（自定义 criteria）
                        —— 这是把咱们领域专业性用 LLM 裁判量化的关键指标

裁判 LLM：自定义 DeepEvalBaseLLM 子类，显式接阿里云百炼 OpenAI 兼容端点
          （deepeval 默认不读 OPENAI_BASE_URL，必须自定义才能用 qwen 裁判）。

数据来源同 ragas（eval_corpus.jsonl）。

【逐条评估 + 断点续评】
  - 每条评完即追加写入 <OUT>_partial.jsonl，中断后重跑可自动续评未完成条；
  - 实时打印 [i/N] 进度，可看到跑到第几。

用法：
  python deepeval_eval.py
  EVAL_LIMIT=5 python deepeval_eval.py        # 先测 5 条
  CHAT_MODEL=deepseek-v4-flash python deepeval_eval.py
  DEEPEVAL_ASYNC=false python deepeval_eval.py # 同步串行（不丢条、不卡死）
"""
import os
import sys
import json
import warnings
import asyncio

warnings.filterwarnings("ignore")
# 关闭 DeepEval 遥测（首次 evaluate 会同步连外部 otel endpoint，离线环境会挂起）
os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "1"
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval import evaluate
from deepeval.evaluate.configs import ErrorConfig, DisplayConfig, AsyncConfig
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    HallucinationMetric,
    GEval,
)
from deepeval.test_case import LLMTestCase, SingleTurnParams

BASE_URL = os.getenv("OPENAI_BASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen3.6-flash-2026-04-16")
LIMIT = int(os.getenv("EVAL_LIMIT", "0") or 0)
# 评估执行方式（env 可控，便于排查异步丢条问题）
RUN_ASYNC = os.getenv("DEEPEVAL_ASYNC", "true").lower() == "true"
MAX_CONCURRENT = int(os.getenv("DEEPEVAL_CONCURRENCY", "5"))
THROTTLE = float(os.getenv("DEEPEVAL_THROTTLE", "0"))
OUT_FILE = os.getenv("DEEPEVAL_OUT", "deepeval_scores.json")


class QwenJudgeLLM(DeepEvalBaseLLM):
    """把阿里云百炼(qwen)当 DeepEval 的裁判 LLM。"""

    def __init__(self):
        # timeout=60: 任何一次调用挂死最多 60s 即失败，不再耗 30 分钟；
        # max_retries=2: 瞬时 429/超时自动重试，尽量把 64 条都评到
        self._client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=60, max_retries=2)
        self._aclient = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=60, max_retries=2)
        self._model = CHAT_MODEL

    def load_model(self, *args, **kwargs):
        # 已在 __init__ 中创建 OpenAI 客户端；此处幂等返回自身
        if getattr(self, "_client", None) is None:
            self._client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=60, max_retries=2)
        if getattr(self, "_aclient", None) is None:
            self._aclient = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=60, max_retries=2)
        self._model = CHAT_MODEL
        return self

    def get_model_name(self):
        return self._model

    def generate(self, prompt: str, schema=None):
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            return resp.choices[0].message.content or ""
        except Exception:
            # 失败返回空串：让指标不崩、该 test case 仍计入（不整条丢弃）
            return ""

    async def a_generate(self, prompt: str, schema=None):
        try:
            resp = await self._aclient.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            return resp.choices[0].message.content or ""
        except Exception:
            return ""

    def generate_with_schema(self, prompt: str, schema: type):
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        return schema.model_validate_json(resp.choices[0].message.content or "{}")

    async def a_generate_with_schema(self, prompt: str, schema: type):
        resp = await self._aclient.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        return schema.model_validate_json(resp.choices[0].message.content or "{}")

    def batch_generate(self, prompts, schema=None):
        return [self.generate(p, schema) for p in prompts]


def load_jsonl(p: Path):
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_metrics(judge):
    return [
        FaithfulnessMetric(model=judge, threshold=0.5),
        AnswerRelevancyMetric(model=judge, threshold=0.5),
        ContextualPrecisionMetric(model=judge, threshold=0.5),
        ContextualRecallMetric(model=judge, threshold=0.5),
        HallucinationMetric(model=judge, threshold=0.5),
        GEval(
            name="专业度",
            criteria=(
                "评估羽球装备导购回答的专业度：是否准确理解并使用羽毛球拍参数"
                "（重量/中杆硬度/平衡点/拍框材质/拉线磅数）、是否给出可执行且"
                "适配用户水平与打法的建议、是否避免笼统或错误断言、是否诚实标注边界。"
            ),
            evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
            model=judge,
            threshold=0.5,
        ),
    ]


def build_case(c):
    return LLMTestCase(
        input=c["user_query"],
        actual_output=c["answer"],
        expected_output=c.get("reference") or "",
        retrieval_context=c["retrieved_contexts"],
        context=c["retrieved_contexts"],
    )


def parse_case_result(result):
    """从单条 evaluate 结果里取各指标分数。返回 (metrics_dict, n_metrics)。"""
    agg = {}
    try:
        trs = getattr(result, "test_results", []) or []
        if not trs:
            return {}, 0
        for md in (trs[0].metrics_data or []):
            name = getattr(md, "name", None) or getattr(md, "metric", None)
            score = getattr(md, "score", None)
            if name and score is not None:
                agg[name] = round(float(score), 4)
    except Exception as e:
        print(f"    [WARN] 单条解析异常: {e}")
    return agg, len(agg)


def main():
    corpus_path = HERE / "eval_corpus.jsonl"
    if not corpus_path.exists():
        raise SystemExit(f"缺少语料: {corpus_path}（请先跑 build_eval_corpus.py）")
    corpus = load_jsonl(corpus_path)
    usable = [c for c in corpus if (c.get("retrieved_contexts") or [])]
    if LIMIT > 0:
        usable = usable[:LIMIT]
    print(f"语料总条数={len(corpus)} | 含检索上下文(可用)={len(usable)} | 本次跑={len(usable)}")

    judge = QwenJudgeLLM()
    metrics = build_metrics(judge)

    # 断点文件：每条评完即追加一行 jsonl；中断后重跑可自动续评未完成的
    out_path = HERE / OUT_FILE
    partial_path = HERE / (out_path.stem + "_partial.jsonl")
    done_ids = set()
    if partial_path.exists():
        try:
            for line in partial_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    done_ids.add(int(json.loads(line).get("idx")))
            if done_ids:
                print(f"发现断点文件，已评 {len(done_ids)} 条，将续评剩余。")
        except Exception as e:
            print(f"  [WARN] 读取断点失败，忽略: {e}")
            done_ids.clear()

    n_total = len(usable)
    for i, c in enumerate(usable):
        if i in done_ids:
            print(f"[{i + 1}/{n_total}] 跳过(已评) {c['user_query'][:24]}")
            continue
        print(f"[{i + 1}/{n_total}] 评估中: {c['user_query'][:30]}", flush=True)
        try:
            result = evaluate(
                test_cases=[build_case(c)],
                metrics=metrics,
                error_config=ErrorConfig(ignore_errors=True),
                display_config=DisplayConfig(
                    show_indicator=False,
                    print_results=False,
                    inspect_after_run=False,
                    truncate_passing_cases=False,
                ),
                async_config=AsyncConfig(
                    run_async=RUN_ASYNC,
                    max_concurrent=MAX_CONCURRENT,
                    throttle_value=THROTTLE,
                ),
            )
            mdict, n_m = parse_case_result(result)
        except Exception as e:
            # 单条整体崩溃也记录，不中断整个循环
            print(f"    [ERROR] 第 {i + 1} 条 evaluate 异常: {e}")
            mdict, n_m = {}, 0

        rec = {
            "idx": i,
            "user_query": c["user_query"],
            "n_metrics": n_m,
            "metrics": mdict,
        }
        with partial_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"    -> 已评 {n_m} 个指标: {mdict}", flush=True)

    # 全部评完后，汇总写出最终报告（即使中断，也已逐条落盘）
    records = []
    if partial_path.exists():
        for line in partial_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
    agg = {}
    for r in records:
        for name, sc in (r.get("metrics") or {}).items():
            agg.setdefault(name, []).append(float(sc))
    scores = {k: (round(sum(v) / len(v), 4) if v else None) for k, v in agg.items()}
    report = {
        "framework": "deepeval",
        "deepeval_version": getattr(__import__("deepeval"), "__version__", "?"),
        "judge_model": CHAT_MODEL,
        "judge_endpoint": BASE_URL,
        "n_input": len(usable),
        "n_evaluated": len(records),
        "run_async": RUN_ASYNC,
        "max_concurrent": MAX_CONCURRENT,
        "metrics": scores,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已写出汇总: {out_path}")
    print(f"断点明细: {partial_path}（{len(records)} 条）")


if __name__ == "__main__":
    main()
