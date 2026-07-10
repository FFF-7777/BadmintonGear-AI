import unittest

from services.rag_pipeline import (
    RetrievalCandidate,
    analyze_query,
    classify_question_scope,
    reciprocal_rank_fusion,
    rerank_candidates,
    rewrite_query_for_retrieval,
    split_knowledge_sections,
)
from services.ai_service import AIService
from langchain_core.documents import Document


class QueryAnalysisTests(unittest.TestCase):
    def test_short_follow_up_uses_previous_user_message(self):
        analysis = analyze_query(
            "中杆硬度呢？",
            history=[
                {"role": "user", "content": "预算 800 想选一支速度快的球拍"},
                {"role": "assistant", "content": "可以优先看 4U 均衡或头轻拍。"},
            ],
        )

        self.assertEqual(analysis.category, "racket")
        self.assertIn("预算 800", analysis.queries[-1])
        self.assertIn("中杆", analysis.queries[-1])

    def test_model_query_extracts_alias_tokens(self):
        analysis = analyze_query("YY 天斧77 Pro 和 JS-12 有什么区别？")

        self.assertIn("AX77PRO", analysis.model_tokens)
        self.assertIn("JS12", analysis.model_tokens)
        self.assertEqual(analysis.compare_targets[:2], ["AX77PRO", "JS12"])

    def test_single_model_query_does_not_become_compare(self):
        analysis = analyze_query("65z3适合宽脚吗")

        self.assertIn("65Z3", analysis.model_tokens)
        self.assertEqual(analysis.compare_targets, [])

    def test_rule_based_query_rewrite_adds_constraints(self):
        rewritten = rewrite_query_for_retrieval("我手腕弱，但是想杀球重一点，买什么拍？")

        self.assertIn("风险约束：手腕力量弱/手腕敏感", rewritten)
        self.assertIn("不应推荐：3U极头重", rewritten)
        self.assertIn("检索关键词", rewritten)

    def test_badminton_general_scope(self):
        self.assertEqual(classify_question_scope("打球前怎么热身比较好？"), "badminton_general")
        self.assertEqual(classify_question_scope("今天天气怎么样"), "offtopic")

    def test_disabled_detail_category_fallback_does_not_recommend_model(self):
        answer = AIService._fallback_answer("新手球鞋推荐什么型号？")

        self.assertIn("具体型号推荐主要覆盖羽毛球拍", answer)
        self.assertIn("不会硬推荐具体型号", answer)

    def test_sources_include_confidence_and_unverified_fields(self):
        sources = AIService._build_sources([
            Document(
                page_content="AX77 Pro 参数",
                metadata={
                    "file_id": 1,
                    "file_name": "球拍库.md",
                    "section_title": "AX77 Pro",
                    "source_confidence": "中高",
                    "unverified_fields": "实时价格,平衡点",
                    "relevance_score": 0.82,
                },
            )
        ])

        self.assertEqual(sources[0]["source_confidence"], "中高")
        self.assertEqual(sources[0]["unverified_fields"], ["实时价格", "平衡点"])


class KnowledgeSplitTests(unittest.TestCase):
    def test_numbered_faq_is_split_by_question(self):
        text = """球拍常见参数
1. 关于平衡点
平衡点越靠近拍头，通常越偏进攻。
2. 关于中杆硬度
新手一般不要优先选择过硬中杆。
3. 关于重量规格
4U 通常更容易挥动，适合大多数业余用户。"""

        sections = split_knowledge_sections(text)

        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0].title, "关于平衡点")
        self.assertNotIn("中杆硬度", sections[0].content)

    def test_model_sections_can_be_split(self):
        text = """AX77 Pro
偏进攻但不算极端，后场下压更轻松。

JS-12
适合双打平抽挡和防守反击。"""

        sections = split_knowledge_sections(text)

        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].title, "AX77 Pro")


class RetrievalRankingTests(unittest.TestCase):
    def test_rrf_deduplicates_same_chunk_from_multiple_routes(self):
        dense = RetrievalCandidate(
            content="4U 均衡球拍更容易上手，适合新手和双打防守。",
            metadata={"chunk_id": "chunk-1", "section_title": "球拍重量"},
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
        analysis = analyze_query("新手双打球拍怎么选？")
        candidates = reciprocal_rank_fusion(
            [[
                RetrievalCandidate(
                    content="新手双打建议优先看 4U、均衡或头轻、甜区更友好的球拍。",
                    metadata={"chunk_id": "relevant", "section_title": "新手球拍"},
                    route="dense",
                    score=0.78,
                ),
                RetrievalCandidate(
                    content="羽毛球速度通常按 76、77 等速度号区分。",
                    metadata={"chunk_id": "irrelevant", "section_title": "羽毛球速度"},
                    route="dense",
                    score=0.72,
                ),
            ]],
        )

        ranked = rerank_candidates(analysis, candidates, top_k=2, threshold=0)

        self.assertEqual(ranked[0].metadata["chunk_id"], "relevant")
        self.assertGreater(ranked[0].final_score, ranked[1].final_score)

    def test_reranker_rejects_low_confidence_candidate(self):
        analysis = analyze_query("宽脚球鞋怎么选？")
        candidates = reciprocal_rank_fusion(
            [[
                RetrievalCandidate(
                    content="球线线径越细，弹性通常更好，但耐打会下降。",
                    metadata={"chunk_id": "string"},
                    route="keyword",
                    score=0.02,
                )
            ]],
        )

        ranked = rerank_candidates(analysis, candidates, top_k=4, threshold=0.2)

        self.assertEqual(ranked, [])

    def test_reranker_does_not_force_fallback_on_model_query(self):
        analysis = analyze_query("AX77PRO 怎么样？")
        candidates = reciprocal_rank_fusion(
            [[
                RetrievalCandidate(
                    content="这是一段完全无关的羽毛球价格说明。",
                    metadata={"chunk_id": "noise"},
                    route="dense",
                    score=0.21,
                )
            ]],
        )

        ranked = rerank_candidates(analysis, candidates, top_k=2, threshold=0.15)

        self.assertEqual(ranked, [])


if __name__ == "__main__":
    unittest.main()
