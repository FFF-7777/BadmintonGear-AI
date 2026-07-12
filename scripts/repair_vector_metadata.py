"""修复本地向量缓存的品类 metadata，不重新计算 embedding。"""
import json
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SERVER_DIR = ROOT_DIR / "server"
sys.path.insert(0, str(SERVER_DIR))
os.chdir(SERVER_DIR)

from services.rag_pipeline import infer_category  # noqa: E402


META_PATH = SERVER_DIR / "chroma_db" / "vector_cache_meta.json"
EQUIPMENT_CATEGORIES = {"racket", "string", "shuttle", "shoes"}


def main() -> None:
    records = json.loads(META_PATH.read_text(encoding="utf-8"))
    changed = 0
    for record in records:
        metadata = record.get("metadata") or {}
        file_name = str(metadata.get("file_name", ""))
        fallback = infer_category(file_name) or "general"
        context = " ".join((
            file_name,
            str(metadata.get("section_title", "")),
            str(record.get("page_content", "")),
        ))
        category = fallback if fallback in EQUIPMENT_CATEGORIES else infer_category(context) or fallback
        if metadata.get("category") != category:
            metadata["category"] = category
            changed += 1

    temp_path = META_PATH.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(META_PATH)
    print(f"OK records={len(records)} metadata_changed={changed} embeddings_unchanged=true")


if __name__ == "__main__":
    main()
