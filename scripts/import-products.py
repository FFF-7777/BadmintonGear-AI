r"""命令行批量导入装备数据。

示例：
python scripts/import-products.py --file D:\data\racket.xlsx --category-id 1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from database import SessionLocal  # noqa: E402
from services.product_import import import_products, parse_import_rows  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="批量导入羽智选装备数据")
    parser.add_argument("--file", required=True, help="xlsx 或 csv 文件路径")
    parser.add_argument("--category-id", type=int, default=None, help="可选，品类ID")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return 1

    rows = parse_import_rows(file_path.name, file_path.read_bytes())
    db = SessionLocal()
    try:
        result = import_products(db, rows, category_id=args.category_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
