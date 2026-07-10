"""Rebuild vector_cache.npz/json.

Default mode tries to copy already stored Chroma embeddings without calling the
embedding API. Use --from-source when Chroma cannot return embeddings reliably.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import chromadb
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from config import CHROMA_COLLECTION, CHROMA_DIR  # noqa: E402
from database import SessionLocal  # noqa: E402
from models.knowledge import KnowledgeFile  # noqa: E402
from services.file_parser import parse_file  # noqa: E402
from services.vector_store import VectorStoreService  # noqa: E402


def _save_cache(ids: list[str], embeddings: np.ndarray, records: list[dict]) -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        CHROMA_DIR / "vector_cache.npz",
        ids=np.array(ids, dtype=str),
        embeddings=embeddings,
    )
    (CHROMA_DIR / "vector_cache_meta.json").write_text(
        json.dumps(records, ensure_ascii=False),
        encoding="utf-8",
    )


def _rebuild_from_chroma() -> tuple[int, int]:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(CHROMA_COLLECTION)
    total = collection.count()
    batch_size = 100
    ids = []
    embedding_rows = []
    documents = []
    metadatas = []
    for offset in range(0, total, batch_size):
        data = collection.get(
            include=["embeddings", "documents", "metadatas"],
            limit=batch_size,
            offset=offset,
        )
        ids.extend(str(item) for item in data.get("ids", []))
        embedding_rows.extend(data.get("embeddings") or [])
        documents.extend(data.get("documents") or [])
        metadatas.extend(data.get("metadatas") or [])

    embeddings = np.array(embedding_rows, dtype="float32")

    if len(ids) == 0 or embeddings.shape[0] != len(ids):
        raise RuntimeError(f"Chroma embeddings 数量异常: ids={len(ids)}, embeddings={embeddings.shape}")
    if len(documents) != len(ids) or len(metadatas) != len(ids):
        raise RuntimeError(
            f"Chroma 记录数量不一致: ids={len(ids)}, documents={len(documents)}, metadatas={len(metadatas)}"
        )

    records = [
        {"page_content": document or "", "metadata": metadata or {}}
        for document, metadata in zip(documents, metadatas)
    ]
    _save_cache(ids, embeddings, records)
    return len(records), embeddings.shape[1] if embeddings.ndim == 2 else 0


def _rebuild_from_sources() -> tuple[int, int]:
    service = VectorStoreService()
    db = SessionLocal()
    try:
        files = (
            db.query(KnowledgeFile)
            .filter(KnowledgeFile.status == 1)
            .order_by(KnowledgeFile.id.asc())
            .all()
        )
    finally:
        db.close()

    ids: list[str] = []
    records: list[dict] = []
    texts: list[str] = []
    for item in files:
        text = parse_file(item.file_path, item.file_type)
        documents = service._build_documents(text, item.id, item.file_name, item.file_type)
        for document in documents:
            ids.append(str(document.metadata["chunk_id"]))
            texts.append(document.page_content)
            records.append({"page_content": document.page_content, "metadata": dict(document.metadata)})

    if not texts:
        raise RuntimeError("没有可重建 cache 的已向量化知识文件")
    embeddings = np.array(service.embeddings.embed_documents(texts), dtype="float32")
    if embeddings.shape[0] != len(ids):
        raise RuntimeError(f"Embedding 数量不一致: ids={len(ids)}, embeddings={embeddings.shape}")
    _save_cache(ids, embeddings, records)
    return len(records), embeddings.shape[1] if embeddings.ndim == 2 else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="重建本地 vector_cache 兜底快照")
    parser.add_argument("--from-source", action="store_true", help="从知识库源文件重新 embedding，仅重建 cache")
    args = parser.parse_args()

    if args.from_source:
        count, dim = _rebuild_from_sources()
    else:
        count, dim = _rebuild_from_chroma()
    print(f"OK rebuilt vector_cache records={count} dim={dim}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
