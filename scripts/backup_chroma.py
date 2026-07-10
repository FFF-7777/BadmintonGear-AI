#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backup the local Chroma vector store, including the numpy fallback cache."""

from __future__ import annotations

import datetime as _dt
import json
import shutil
import sqlite3
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "server" / "chroma_db"
DEST_PARENT = ROOT / "backups"


def count_embeddings(sqlite_path: Path) -> int:
    try:
        with sqlite3.connect(sqlite_path) as con:
            return int(con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0])
    except Exception:
        return -1


def sqlite_integrity(sqlite_path: Path) -> str:
    try:
        with sqlite3.connect(sqlite_path) as con:
            return str(con.execute("PRAGMA integrity_check").fetchone()[0])
    except Exception as exc:
        return f"error: {exc}"


def count_cache(chroma_dir: Path) -> tuple[int, int]:
    npz_path = chroma_dir / "vector_cache.npz"
    meta_path = chroma_dir / "vector_cache_meta.json"
    if not npz_path.exists() or not meta_path.exists():
        return -1, -1
    vectors = np.load(npz_path, allow_pickle=False)
    records = json.loads(meta_path.read_text(encoding="utf-8"))
    return int(vectors["embeddings"].shape[0]), len(records)


def directory_stats(path: Path) -> tuple[int, int]:
    total_size = 0
    file_count = 0
    for item in path.rglob("*"):
        if item.is_file():
            total_size += item.stat().st_size
            file_count += 1
    return total_size, file_count


def main() -> None:
    force = "--force" in sys.argv
    if not SRC.is_dir():
        print(f"[错误] 源目录不存在: {SRC}")
        sys.exit(1)

    sqlite_path = SRC / "chroma.sqlite3"
    if not sqlite_path.exists():
        print(f"[错误] 未找到 Chroma SQLite 文件: {sqlite_path}")
        sys.exit(1)

    embedding_count = count_embeddings(sqlite_path)
    if embedding_count <= 0 and not force:
        print(f"[警告] 当前向量库 embeddings={embedding_count}，不建议备份空库。")
        print("        如确实要备份空库，请加 --force。")
        sys.exit(1)

    integrity = sqlite_integrity(sqlite_path)
    if integrity != "ok" and not force:
        print(f"[错误] chroma.sqlite3 完整性检查未通过: {integrity}")
        print("        请先修复或确认后再加 --force 备份。")
        sys.exit(1)

    cache_vectors, cache_records = count_cache(SRC)
    if (cache_vectors != embedding_count or cache_records != embedding_count) and not force:
        print("[错误] 本地向量快照不完整，拒绝备份。")
        print(f"        embeddings={embedding_count}, cache_vectors={cache_vectors}, cache_records={cache_records}")
        print("        请重新向量化生成 vector_cache，再备份。")
        sys.exit(1)

    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = DEST_PARENT / f"chroma_db_{timestamp}"
    DEST_PARENT.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC, dest)

    total_size, file_count = directory_stats(dest)
    print(f"[信息] Chroma embeddings: {embedding_count}")
    print(f"[信息] Vector cache records: {cache_records}")
    print(f"[完成] 已备份到: {dest}")
    print(f"        大小: {total_size / 1024 / 1024:.1f} MB，文件数: {file_count}")
    print("        恢复方法: 停后端 -> 删 server/chroma_db/ -> 把本目录复制回去 -> 重启后端")


if __name__ == "__main__":
    main()
