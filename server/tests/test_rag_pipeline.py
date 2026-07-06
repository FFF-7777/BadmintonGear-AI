import unittest

from services.rag_pipeline import (
    RetrievalCandidate,
    analyze_query,
    reciprocal_rank_fusion,
    rerank_candidates,
    split_knowledge_sections,
)


class QueryAnalysisTests(unittest.TestCase):
    def test_short_follow_up_uses_previous_user_message(self):
        analysis = analyze_query(
            "运费谁承担？",
            history=[
                {"role": "user", "content": "装备质量有问题，我想退货"},
                {"role": "assistant", "content": "请提供装备照片。"},
            ],
        )

        self.assertEqual(analysis.category, "after_sale")
        self.assertIn("装备质量有问题", analysis.queries[-1])
        self.assertIn("运费谁承担", analysis.queries[-1])

    def test_logistics_query_is_classified(self):
        analysis = analyze_query("快递显示签收了，但我没有收到")

        self.assertEqual(analysis.category, "logistics")
        self.assertIn("物流", analysis.expanded_query)


class KnowledgeSplitTests(unittest.TestCase):
    def test_numbered_faq_is_split_by_question(self):
        text = """常见物流问题
1. 关于发货延迟
订单会在付款后尽快发出。
2. 关于物流不更新
运输途中可能没有及时扫描。
3. 关于显示签收但未收到
请先检查快递柜和门卫。"""

        sections = split_knowledge_sections(text)

        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0].title, "关于发货延迟")
        self.assertNotIn("物流不更新", sections[0].content)


class RetrievalRankingTests(unittest.TestCase):
    def test_rrf_deduplicates_same_chunk_from_multiple_routes(self):
        dense = RetrievalCandidate(
            content="质量问题退货运费由商家承担",
            metadata={"chunk_id": "chunk-1", "section_title": "退货运费"},
            route="dense",
            score=0.82,
        )
        keyword = RetrievalCandidate(
            content=dense.content,
            metadata=dense.metadata,
            route="keyword",
            score=0.75,
        )

        fused = reciprocal_rank_fusion([[dense], [keyword]], rrf_k=60)

        self.assertEqual(len(fused), 1)
        self.assertEqual(set(fused[0].routes), {"dense", "keyword"})
        self.assertGreater(fused[0].rrf_score, 1 / 61)

    def test_reranker_prefers_relevant_content(self):
        analysis = analyze_query("退货运费谁承担")
        candidates = reciprocal_rank_fusion(
            [[
                RetrievalCandidate(
                    content="质量问题退货时，退货运费由商家承担。",
                    metadata={"chunk_id": "relevant", "section_title": "退货运费"},
                    route="dense",
                    score=0.78,
                ),
                RetrievalCandidate(
                    content="账号注销后积分和优惠券会被清除。",
                    metadata={"chunk_id": "irrelevant", "section_title": "注销账户"},
                    route="dense",
                    score=0.72,
                ),
            ]],
        )

        ranked = rerank_candidates(analysis, candidates, top_k=2, threshold=0)

        self.assertEqual(ranked[0].metadata["chunk_id"], "relevant")
        self.assertGreater(ranked[0].final_score, ranked[1].final_score)

    def test_reranker_rejects_low_confidence_candidate(self):
        analysis = analyze_query("怎么申请开发票")
        candidates = reciprocal_rank_fusion(
            [[
                RetrievalCandidate(
                    content="快递运输途中可能没有及时扫描。",
                    metadata={"chunk_id": "logistics"},
                    route="keyword",
                    score=0.02,
                )
            ]],
        )

        ranked = rerank_candidates(analysis, candidates, top_k=4, threshold=0.2)

        self.assertEqual(ranked, [])


if __name__ == "__main__":
    unittest.main()
