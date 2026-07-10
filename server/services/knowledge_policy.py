"""Rules for deciding which knowledge files may enter the vector store."""
from __future__ import annotations

from pathlib import Path


VECTOR_DOC_FILENAMES = {
    "羽毛球拍商品库_RAG检索_v4_平均价覆盖版.md",
    "羽毛球拍商品库_RAG检索_v5.1_合并定稿版.md",
    "羽毛球拍商品库_RAG检索_v5.2_参数优化版.md",
    "羽毛球拍选拍知识库_RAGv4_平均价覆盖版.md",
    "羽毛球拍参数与型号对比知识库_RAGv4_平均价覆盖版.md",
    "羽毛球综合知识库_规则术语战术训练安全_RAGv4_平均价覆盖版.md",
}

TEST_VECTOR_DOC_FILENAMES = {
    "向量化前先向量化此测试文件.md",
}


def is_vectorizable_knowledge_filename(filename: str) -> bool:
    name = Path(filename or "").name
    suffix = Path(name).suffix.lower()
    if suffix not in {".md", ".markdown"}:
        return False
    return name in VECTOR_DOC_FILENAMES or name in TEST_VECTOR_DOC_FILENAMES


def vectorization_policy_message(filename: str) -> str:
    if is_vectorizable_knowledge_filename(filename):
        return ""
    return (
        "该文件不是本阶段允许进入向量库的 RAG Markdown。"
        "请只向量化 4 个 v4 RAG MD；JSONL/CSV/Excel/README/policy/reports 用于商品导入、规则或人工复核，不进入普通向量库。"
    )
