"""
最小 RAG 评估闭环（P1-5）。

本脚本不修改任何现有代码路径，仅作为"测量"工具，用来在改动检索/精排逻辑前后
量化对比召回质量，避免凭感觉判断优化是否有效。

两种模式：
1. 离线自检（--offline）：不依赖网络与知识库，验证 RRF 融合与六维精排的
   打分数学正确（CI / 本地快速回归用），确保排序逻辑没有被改坏。
2. 在线评测（默认）：对一组 golden query 跑完整检索管线（safe_search），
   检查召回文档是否命中预期信号（关键词 / 分类），输出召回率与覆盖度。
   当前知识库为空时，会如实报告 0 命中——这是预期现象，待知识库在管理后台
   重新上传后，本脚本即可给出有意义的评估。

用法：
  python -m scripts.eval_rag --offline
  python -m scripts.eval_rag                      # 在线评测（需 .env 且已上传知识库）
  python -m scripts.eval_rag --queries my.jsonl   # 用自定义 golden queries
"""
import argparse
import json
import os
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

# 测试/脚本环境兜底 SECRET_KEY，避免 config 启动报错（与 pytest conftest 一致）
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

from services.rag_pipeline import (
    QueryAnalysis,
    RetrievalCandidate,
    reciprocal_rank_fusion,
    rerank_candidates,
    tokenize,
    bm25_scores,
)
from collections import Counter


# ---------------------------------------------------------------------------
# Golden queries（在线评测用）
# expected_keywords：检索结果文本/元数据中应当出现的词元（用于判断"命中"）
# expected_category：可选，期望命中的分类（racket/shoe/string/shuttlecock）
# ---------------------------------------------------------------------------
GOLDEN_QUERIES = [
    {
        "query": "预算600元的新手羽毛球拍推荐",
        "expected_keywords": ["羽毛球拍", "新手", "预算"],
        "expected_category": "racket",
    },
    {
        "query": "双打防守型球拍有什么推荐",
        "expected_keywords": ["防守", "双打", "羽毛球拍"],
        "expected_category": "racket",
    },
    {
        "query": "膝盖不好适合穿什么羽毛球鞋",
        "expected_keywords": ["羽毛球鞋", "缓震", "膝盖"],
        "expected_category": "shoe",
    },
    {
        "query": "尤尼克斯弓箭11和龙刃10怎么选",
        "expected_keywords": ["弓箭", "龙刃", "对比"],
        "expected_category": "racket",
    },
    {
        "query": "耐打的鹅毛羽毛球有哪些",
        "expected_keywords": ["鹅毛", "羽毛球", "耐打"],
        "expected_category": "shuttlecock",
    },
    {
        "query": "高弹球线推荐一下",
        "expected_keywords": ["球线", "高弹"],
        "expected_category": "string",
    },
]


def _make_candidate(content: str, route: str, score: float = 0.5,
                    metadata: dict = None, routes: list = None) -> RetrievalCandidate:
    return RetrievalCandidate(
        content=content,
        metadata=metadata or {},
        route=route,
        score=score,
        routes=routes or [route],
    )


def _make_analysis(expanded_query: str, model_tokens: list = None,
                   compare_targets: list = None, normalized_query: str = None) -> QueryAnalysis:
    return QueryAnalysis(
        original_query=expanded_query,
        normalized_query=normalized_query or expanded_query,
        expanded_query=expanded_query,
        category=None,
        queries=[expanded_query],
        keywords=[],
        scope="equipment",
        model_tokens=model_tokens or [],
        compare_targets=compare_targets or [],
    )


def _run_offline_self_test() -> int:
    """验证 RRF 融合与精排打分的不变量；返回失败计数。"""
    failures = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal failures
        if cond:
            print(f"  [PASS] {name}")
        else:
            failures += 1
            print(f"  [FAIL] {name}  {detail}")

    print("离线自检：RRF 融合")
    c1 = _make_candidate("羽毛球拍 新手 推荐", "dense_original", score=0.8)
    c2 = _make_candidate("防守型 双打 球拍", "dense_original", score=0.6)
    c2_dup = _make_candidate("防守型 双打 球拍", "dense_enhanced", score=0.7)
    c3 = _make_candidate("鹅毛 羽毛球 耐打", "dense_enhanced", score=0.9)
    fused = reciprocal_rank_fusion([[c1, c2], [c2_dup, c3]], rrf_k=60)
    by_content = {c.content: c for c in fused}
    # 不变量1：跨路线同内容被合并，rrf 累加
    check("跨路线合并", "防守型 双打 球拍" in by_content)
    merged = by_content["防守型 双打 球拍"]
    # route A 中 c2 排在 rank2 -> 1/62；route B 中 c2_dup 排在 rank1 -> 1/61
    check("合并后 rrf 累加", abs(merged.rrf_score - (1 / 61 + 1 / 62)) < 1e-9,
          f"got {merged.rrf_score}")
    check("合并后 routes 含两路", set(merged.routes) >= {"dense_original", "dense_enhanced"},
          f"got {merged.routes}")
    check("合并后 score 取最大", abs(merged.score - 0.7) < 1e-9, f"got {merged.score}")
    # 不变量2：排序按 rrf 降序（c2 出现两路，应排第一）
    check("融合排序正确", fused[0].content == "防守型 双打 球拍", f"top={fused[0].content}")

    print("离线自检：六维精排")
    # 强相关文档（含全部查询词 + 型号匹配）应排在非相关文档之前
    qa = _make_analysis("尤尼克斯 弓箭11 参数", model_tokens=["弓箭11"])
    strong = _make_candidate(
        "尤尼克斯 弓箭11 是一款平衡型羽毛球拍，适合进阶选手。",
        "dense_original", score=0.9,
        metadata={"model_tokens": ["弓箭11"], "section_title": "弓箭11 参数", "brand": "尤尼克斯"},
    )
    weak = _make_candidate(
        "今天天气不错，适合去球馆打球。",
        "dense_original", score=0.3,
        metadata={},
    )
    ranked = rerank_candidates(qa, [weak, strong], top_k=10, threshold=0.15)
    check("精排返回非空", bool(ranked))
    check("强相关排前", ranked[0].content.startswith("尤尼克斯 弓箭11"),
          f"top={ranked[0].content if ranked else None}")
    check("final_score 在[0,1]", all(0.0 <= c.final_score <= 1.0 for c in ranked))
    check("强相关 confidence>阈值", strong.confidence >= 0.15, f"conf={strong.confidence:.3f}")

    print("离线自检：阈值过滤")
    # 高阈值 + 低质文档 → 全部被过滤；且因无 model_tokens，仍可能回退到 top_k
    qb = _make_analysis("羽毛球")
    low = _make_candidate("完全无关的内容 xyz", "dense_original", score=0.2, metadata={})
    # 短查询(<=6字)会使 effective_threshold *= 0.7
    q_short = _make_analysis("羽毛球", normalized_query="羽毛球")
    filtered_short = rerank_candidates(q_short, [low], top_k=5, threshold=0.5)
    filtered_long = rerank_candidates(qb, [low], top_k=5, threshold=0.5)
    check("低质文档被阈值过滤(长查询)",
          len(filtered_long) == 0, f"got {len(filtered_long)}")
    check("短查询阈值放宽仍过滤无关内容",
          len(filtered_short) == 0, f"got {len(filtered_short)}")

    print("离线自检：型号/对比类低置信度不兜底")
    qm = _make_analysis("某不存在型号X参数", model_tokens=["型号X"])
    only_weak = _make_candidate("无关内容", "dense_original", score=0.2, metadata={})
    res = rerank_candidates(qm, [only_weak], top_k=5, threshold=0.15)
    check("型号类低置信度返回空(不兜底)", res == [],
          f"got {len(res)} (应不硬推不相关结果)")

    print("离线自检：BM25 关键词打分")
    # 语料：d0 含稀有判别词"弓箭11"；d1 仅含常见词"羽毛球"(出现在所有文档)；d2 含"新手"
    d0 = Counter(["弓箭11", "羽毛球拍", "平衡", "羽毛球"])
    d1 = Counter(["羽毛球", "打球", "运动", "羽毛球"])
    d2 = Counter(["新手", "入门", "羽毛球拍", "羽毛球"])
    corpus = [d0, d1, d2]
    doc_freq = {}
    for c in corpus:
        for t in c:
            doc_freq[t] = doc_freq.get(t, 0) + 1
    doc_lens = [sum(c.values()) for c in corpus]
    sc = bm25_scores(["弓箭11", "羽毛球拍"], corpus, doc_freq, doc_lens)
    check("BM25 稀有判别词文档得分最高", sc[0] > sc[1] and sc[0] > sc[2], f"scores={sc}")
    check("BM25 纯常见词文档得分最低", sc[1] == min(sc), f"scores={sc}")

    print(f"离线自检完成：{failures} 个失败")
    return failures


def _hit_expected(documents: list, expected: dict) -> dict:
    """判断一条 golden query 的检索结果是否命中预期信号。"""
    if not documents:
        return {"doc_hit": False, "keyword_hit": False, "category_hit": False}
    blob = " ".join(
        str(d.page_content) + " " + " ".join(str(v) for v in d.metadata.values())
        for d in documents
    )
    blob_tokens = tokenize(blob)
    kw_hit = any(tokenize(k) & blob_tokens for k in expected.get("expected_keywords", []))
    cat = expected.get("expected_category")
    cat_hit = cat is not None and any(
        d.metadata.get("category") == cat for d in documents
    )
    return {"doc_hit": True, "keyword_hit": kw_hit, "category_hit": cat_hit}


def _run_live_eval(queries_path: str = None) -> int:
    """在线评测：跑完整检索管线，统计命中率。需 .env 与已上传知识库。"""
    try:
        from services.vector_store import safe_search
    except Exception as exc:  # pragma: no cover
        print(f"无法导入检索模块：{exc}")
        return 1

    if queries_path:
        with open(queries_path, "r", encoding="utf-8") as fh:
            queries = [json.loads(line) for line in fh if line.strip()]
    else:
        queries = GOLDEN_QUERIES

    total = len(queries)
    kw_hits = 0
    cat_hits = 0
    nonempty = 0
    print(f"\n在线评测：共 {total} 条 golden query\n" + "-" * 60)
    for item in queries:
        q = item["query"]
        try:
            result = safe_search(q, top_k=5, timeout=40)
        except Exception as exc:
            print(f"  [ERR ] {q} -> {exc}")
            continue
        docs = getattr(result, "documents", []) or []
        if docs:
            nonempty += 1
        stats = _hit_expected(docs, item)
        kw_hits += int(stats["keyword_hit"])
        cat_hits += int(stats["category_hit"])
        status = "命中" if stats["keyword_hit"] or stats["category_hit"] else "未命中"
        print(f"  [{status}] {q}  (召回 {len(docs)} 篇)")

    print("-" * 60)
    print(f"召回非空查询: {nonempty}/{total}")
    print(f"关键词命中率: {kw_hits}/{total} ({100.0 * kw_hits / total:.1f}%)")
    print(f"分类命中率:   {cat_hits}/{total} ({100.0 * cat_hits / total:.1f}%)")
    if nonempty == 0:
        print("提示：当前知识库为空（chroma_db 已清空待重新上传），0 命中属预期。"
              "在管理后台重新上传知识库文件后，再运行本脚本即可得到有意义的评估。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG 最小评估闭环")
    parser.add_argument("--offline", action="store_true", help="仅跑离线打分自检（不需网络/KB）")
    parser.add_argument("--queries", help="自定义 golden queries 的 JSONL 路径")
    args = parser.parse_args()

    if args.offline:
        print("=== 离线自检模式 ===")
        return 1 if _run_offline_self_test() else 0

    print("=== 在线评测模式 ===")
    return _run_live_eval(args.queries)


if __name__ == "__main__":
    sys.exit(main())
