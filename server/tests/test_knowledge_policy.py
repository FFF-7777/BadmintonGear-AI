import unittest

from services.knowledge_policy import is_vectorizable_knowledge_filename


class KnowledgePolicyTests(unittest.TestCase):
    def test_only_v4_rag_markdown_and_test_file_are_vectorizable(self):
        allowed = [
            "羽毛球拍商品库_RAG检索_v4_平均价覆盖版.md",
            "羽毛球拍商品库_RAG检索_v5.1_合并定稿版.md",
            "羽毛球拍商品库_RAG检索_v5.2_参数优化版.md",
            "羽毛球拍选拍知识库_RAGv4_平均价覆盖版.md",
            "羽毛球拍参数与型号对比知识库_RAGv4_平均价覆盖版.md",
            "羽毛球综合知识库_规则术语战术训练安全_RAGv4_平均价覆盖版.md",
            "向量化前先向量化此测试文件.md",
        ]
        blocked = [
            "羽毛球拍商品库_结构化_v4_平均价覆盖版.jsonl",
            "README_v4_平均价覆盖版说明.md",
            "羽毛球拍RAG边界规则与回答模板_v4_平均价覆盖版.md",
            "已按平均值覆盖价格_清单与知识库.csv",
        ]

        self.assertTrue(all(is_vectorizable_knowledge_filename(name) for name in allowed))
        self.assertFalse(any(is_vectorizable_knowledge_filename(name) for name in blocked))


if __name__ == "__main__":
    unittest.main()
