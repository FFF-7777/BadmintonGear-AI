"""Rebuild the local v4 RAG vector store in a fixed safe order.

Usage:
  python scripts/rebuild_v4_knowledge.py --test-only --clear
  python scripts/rebuild_v4_knowledge.py --final --clear
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from config import CHROMA_DIR  # noqa: E402
from database import SessionLocal  # noqa: E402
from models.knowledge import KnowledgeFile  # noqa: E402
from services.file_parser import get_file_type, parse_file  # noqa: E402
from services.knowledge_policy import is_vectorizable_knowledge_filename  # noqa: E402
from services.rag_pipeline import extract_model_tokens, infer_brand, infer_doc_type, infer_series  # noqa: E402


TEST_DOC = ROOT / "知识库" / "向量化前先向量化此测试文件.md"
V4_ROOT = ROOT / "知识库" / "badminton_kb_final_v4_avg_price"
FINAL_DOCS = [
    V4_ROOT / "product" / "羽毛球拍商品库_RAG检索_v5.2_参数优化版.md",
    V4_ROOT / "guide" / "羽毛球拍选拍知识库_RAGv4_平均价覆盖版.md",
    V4_ROOT / "guide" / "羽毛球拍参数与型号对比知识库_RAGv4_平均价覆盖版.md",
    V4_ROOT / "general" / "羽毛球综合知识库_规则术语战术训练安全_RAGv4_平均价覆盖版.md",
]


def _resolve_inside_workspace(path: Path) -> Path:
    resolved = path.resolve()
    resolved.relative_to(ROOT.resolve())
    return resolved


def _clear_vector_store_and_records() -> None:
    chroma_dir = _resolve_inside_workspace(CHROMA_DIR)
    if chroma_dir.name != "chroma_db" or chroma_dir.parent != SERVER_DIR:
        raise RuntimeError(f"拒绝清空异常向量目录: {chroma_dir}")
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)
    chroma_dir.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        db.query(KnowledgeFile).delete()
        db.commit()
    finally:
        db.close()


def _vectorize_one(path: Path) -> tuple[int, int]:
    from services.vector_store import safe_add_documents  # Imported after optional clear.

    resolved = _resolve_inside_workspace(path)
    if not resolved.exists():
        raise FileNotFoundError(f"文件不存在: {resolved}")
    if not is_vectorizable_knowledge_filename(resolved.name):
        raise ValueError(f"不允许向量化该文件: {resolved.name}")

    file_type = get_file_type(resolved.name)
    text = parse_file(str(resolved), file_type)
    initial_text = f"{resolved.name} {text[:2000]}"
    model_aliases = extract_model_tokens(initial_text)

    db = SessionLocal()
    try:
        kf = KnowledgeFile(
            file_name=resolved.name,
            file_type=file_type,
            file_path=str(resolved).replace("\\", "/"),
            brand=infer_brand(initial_text) or None,
            series=infer_series(initial_text) or None,
            model_aliases=",".join(model_aliases) if model_aliases else None,
            doc_type=infer_doc_type(initial_text),
            file_size=resolved.stat().st_size,
            status=0,
        )
        db.add(kf)
        db.commit()
        db.refresh(kf)

        chunk_count, add_err = safe_add_documents(text, kf.id, kf.file_name, kf.file_type)
        if add_err:
            kf.status = 2
            kf.chunk_count = 0
            kf.error_msg = str(add_err)[:500]
            db.commit()
            raise RuntimeError(f"{resolved.name} 向量化失败: {kf.error_msg}")

        kf.status = 1
        kf.chunk_count = chunk_count
        kf.error_msg = None
        db.commit()
        return kf.id, chunk_count
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="重建 v4 羽毛球拍 RAG 向量库")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--test-only", action="store_true", help="只向量化测试 MD")
    mode.add_argument("--final", action="store_true", help="向量化 4 个 v4 RAG MD")
    parser.add_argument("--clear", action="store_true", help="先清空 chroma_db 和知识库记录")
    args = parser.parse_args()

    docs = [TEST_DOC] if args.test_only else FINAL_DOCS
    if args.clear:
        _clear_vector_store_and_records()
        print("已清空 server/chroma_db 和 t_knowledge_file 记录")

    for path in docs:
        file_id, chunks = _vectorize_one(path)
        print(f"OK file_id={file_id} chunks={chunks} {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
