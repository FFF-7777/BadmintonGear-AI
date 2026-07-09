"""装备批量导入与模板生成服务。"""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

from sqlalchemy.orm import Session

from models.product import Product
from services.rag_pipeline import CATEGORY_NAME_BY_ID, infer_brand, infer_series, normalize_model_token
from services.recommendation import serialize_product_card

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
ALLOWED_IMPORT_EXTS = {".xlsx", ".csv"}

COMMON_FIELDS = [
    "name",
    "brand",
    "series",
    "model_aliases",
    "description",
    "price",
    "image",
    "images",
    "source_url",
    "source_note",
    "manual_tags",
]

CATEGORY_SPEC_FIELDS = {
    1: [
        "weight_class", "balance", "shaft_flex", "length", "max_tension", "material",
        "frame_material", "shaft_material", "suitable_level", "suitable_style", "play_type",
        "highlight", "contraindications",
    ],
    2: [
        "gauge", "feel", "repulsion", "durability", "hitting_sound", "control",
        "tension_range", "suitable_level", "suitable_style",
    ],
    3: [
        "material", "speed", "durability", "flight", "stability", "usage_scene", "temperature_hint",
    ],
    4: [
        "cushion_score", "support_score", "grip_score", "ankle_support", "last_shape", "width_fit",
        "weight", "upper_material", "suitable_level",
    ],
}

ENUM_LIST_FIELDS = {"model_aliases", "manual_tags", "images", "suitable_level", "suitable_style", "play_type"}
DECIMAL_FIELDS = {"price", "cushion_score", "support_score", "grip_score"}
SPEC_FLOAT_FIELDS = {"cushion_score", "support_score", "grip_score"}
SPEC_INTEGER_FIELDS = set()

TEMPLATE_EXAMPLES = {
    1: {
        "name": "YONEX 天斧 77 Pro（示例）",
        "brand": "YONEX",
        "series": "天斧",
        "model_aliases": "AX77PRO, ASTROX 77 PRO, 天斧77PRO",
        "description": "偏进攻但不极端，适合后场下压。",
        "price": "1099",
        "image": "/uploads/product/astrox77pro.png",
        "source_url": "https://example.com/astrox77pro",
        "source_note": "品牌页",
        "manual_tags": "进攻,进阶",
        "weight_class": "4U",
        "balance": "head-heavy",
        "shaft_flex": "medium",
        "length": "675",
        "max_tension": "28",
        "material": "high_modulus_graphite",
        "frame_material": "HM Graphite",
        "shaft_material": "HM Graphite",
        "suitable_level": "intermediate,advanced",
        "suitable_style": "attack,balanced",
        "play_type": "singles,doubles",
        "highlight": "后场下压、杀球扎实",
        "contraindications": "纯新手或手腕力量不足者慎选",
    },
    2: {
        "name": "YONEX BG80（示例）",
        "brand": "YONEX",
        "model_aliases": "BG80",
        "description": "经典进攻线，击球反馈直接。",
        "price": "58",
        "manual_tags": "高弹,耐打",
        "gauge": "0.68",
        "feel": "hard",
        "repulsion": "high",
        "durability": "high",
        "hitting_sound": "crisp",
        "control": "good",
        "tension_range": "22-28",
        "suitable_level": "intermediate,advanced",
        "suitable_style": "attack,control",
    },
    3: {
        "name": "亚狮龙 7 号（示例）",
        "brand": "RSL",
        "series": "7号",
        "description": "训练与俱乐部常用训练球。",
        "price": "118",
        "manual_tags": "训练,稳定",
        "material": "goose_feather",
        "speed": "77",
        "durability": "high",
        "flight": "stable",
        "stability": "good",
        "usage_scene": "训练",
        "temperature_hint": "常温馆",
    },
    4: {
        "name": "YONEX 65Z3（示例）",
        "brand": "YONEX",
        "series": "65Z",
        "model_aliases": "65Z3, POWER CUSHION 65Z3",
        "description": "缓震与包裹兼顾，适合高频移动。",
        "price": "799",
        "manual_tags": "高缓震,比赛",
        "cushion_score": "9.2",
        "support_score": "8.8",
        "grip_score": "8.7",
        "ankle_support": "medium",
        "last_shape": "regular",
        "width_fit": "regular",
        "weight": "350",
        "upper_material": "mesh+synthetic",
        "suitable_level": "intermediate,advanced",
    },
}

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


@dataclass
class ImportErrorRow:
    row: int
    field: str
    reason: str


def template_headers(category_id: int) -> List[str]:
    return COMMON_FIELDS + CATEGORY_SPEC_FIELDS[category_id]


def _column_name(index: int) -> str:
    result = ""
    current = index + 1
    while current:
        current, remainder = divmod(current - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _sheet_row_xml(row_index: int, values: Sequence[str]) -> str:
    cells = []
    for col_index, value in enumerate(values):
        ref = f"{_column_name(col_index)}{row_index}"
        safe_value = xml_escape(str(value or ""))
        cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{safe_value}</t></is></c>')
    return f'<row r="{row_index}">{"".join(cells)}</row>'


def build_template_xlsx(category_id: int) -> bytes:
    headers = template_headers(category_id)
    example = TEMPLATE_EXAMPLES.get(category_id, {})
    rows_xml = [
        _sheet_row_xml(1, headers),
        _sheet_row_xml(2, [example.get(header, "") for header in headers]),
    ]
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(rows_xml)}</sheetData>'
        "</worksheet>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="装备导入模板" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/></Relationships>'
    )
    package_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", package_rels)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buffer.getvalue()


def _parse_shared_strings(zf: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    values = []
    for item in root.findall(f".//{{{NS_MAIN}}}si"):
        text = "".join(node.text or "" for node in item.findall(f".//{{{NS_MAIN}}}t"))
        values.append(text)
    return values


def _cell_text(cell: ET.Element, shared_strings: Sequence[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(f".//{{{NS_MAIN}}}t"))
    raw = cell.findtext(f"{{{NS_MAIN}}}v", default="") or ""
    if cell_type == "s":
        try:
            return shared_strings[int(raw)]
        except (ValueError, IndexError):
            return ""
    return raw


def _sheet_path(zf: zipfile.ZipFile) -> str:
    for name in zf.namelist():
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
            return name
    raise ValueError("Excel 文件中未找到工作表")


def parse_xlsx_rows(raw_bytes: bytes) -> List[Dict[str, str]]:
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
        shared_strings = _parse_shared_strings(zf)
        root = ET.fromstring(zf.read(_sheet_path(zf)))

    rows: List[List[str]] = []
    for row in root.findall(f".//{{{NS_MAIN}}}row"):
        values: List[str] = []
        current_col = 0
        for cell in row.findall(f"{{{NS_MAIN}}}c"):
            ref = cell.attrib.get("r", "")
            col_letters = "".join(ch for ch in ref if ch.isalpha())
            target_col = 0
            for ch in col_letters:
                target_col = target_col * 26 + (ord(ch.upper()) - 64)
            target_col = max(target_col - 1, current_col)
            while current_col < target_col:
                values.append("")
                current_col += 1
            values.append(_cell_text(cell, shared_strings).strip())
            current_col += 1
        rows.append(values)

    if not rows:
        return []
    headers = [header.strip() for header in rows[0]]
    result: List[Dict[str, str]] = []
    for values in rows[1:]:
        if not any(str(value).strip() for value in values):
            continue
        padded = values + [""] * max(0, len(headers) - len(values))
        result.append({headers[index]: padded[index].strip() for index in range(len(headers)) if headers[index]})
    return result


def parse_csv_rows(raw_bytes: bytes) -> List[Dict[str, str]]:
    text = raw_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [{key.strip(): (value or "").strip() for key, value in row.items() if key} for row in reader]


def parse_import_rows(filename: str, raw_bytes: bytes) -> List[Dict[str, str]]:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_IMPORT_EXTS:
        raise ValueError("仅支持 xlsx 或 csv 导入")
    if ext == ".xlsx":
        return parse_xlsx_rows(raw_bytes)
    return parse_csv_rows(raw_bytes)


def infer_import_category(headers: Iterable[str]) -> Optional[int]:
    header_set = set(headers)
    best_category = None
    best_score = 0
    for category_id, spec_fields in CATEGORY_SPEC_FIELDS.items():
        score = len(header_set & set(spec_fields))
        if score > best_score:
            best_category = category_id
            best_score = score
    return best_category if best_score > 0 else None


def _split_list(value: str) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"[,，/|]", value) if part.strip()]


def _normalize_spec_value(field: str, value: str):
    if field in ENUM_LIST_FIELDS:
        return _split_list(value)
    if field in SPEC_FLOAT_FIELDS and value:
        return float(value)
    if field in SPEC_INTEGER_FIELDS and value:
        return int(value)
    return value.strip()


def _validate_row(row_index: int, category_id: int, row: Dict[str, str], existing_products: Sequence[Product]) -> List[ImportErrorRow]:
    errors: List[ImportErrorRow] = []
    if not row.get("name"):
        errors.append(ImportErrorRow(row_index, "name", "装备名称不能为空"))
    # price 为"建议必填项"：仅做格式校验，缺失不阻断（落库默认 0）
    price_raw = (row.get("price") or "").strip()
    if price_raw:
        try:
            Decimal(price_raw)
        except (InvalidOperation, ValueError):
            errors.append(ImportErrorRow(row_index, "price", "参考价格式不正确"))

    # 品类规格字段为"建议必填项"，缺失不再硬性阻断导入，
    # 仅让 specs 对应键留空（落库后仍可按型号名/品牌被检索）。

    incoming_aliases = {normalize_model_token(alias) for alias in _split_list(row.get("model_aliases", ""))}
    for product in existing_products:
        if product.name == row.get("name"):
            errors.append(ImportErrorRow(row_index, "name", f"与现有装备重名：{product.name}"))
            break
        existing_aliases = {normalize_model_token(alias) for alias in (product.model_aliases or [])}
        overlap = incoming_aliases & existing_aliases
        if overlap:
            errors.append(ImportErrorRow(row_index, "model_aliases", f"与现有装备别名冲突：{', '.join(sorted(overlap))}"))
            break
    return errors


def _build_product_payload(category_id: int, row: Dict[str, str]) -> Dict:
    specs = {}
    for field in CATEGORY_SPEC_FIELDS[category_id]:
        value = (row.get(field) or "").strip()
        if value == "":
            continue
        specs[field] = _normalize_spec_value(field, value)

    brand = (row.get("brand") or "").strip() or infer_brand(row.get("name", "")) or ""
    series = (row.get("series") or "").strip() or infer_series(f"{row.get('name', '')} {row.get('description', '')}") or ""
    return {
        "category_id": category_id,
        "name": row.get("name", "").strip(),
        "brand": brand,
        "series": series,
        "model_aliases": _split_list(row.get("model_aliases", "")),
        "description": row.get("description", "").strip() or None,
        "specs": specs,
        "price": Decimal(str(row.get("price", "0")).strip() or "0"),
        "image": row.get("image", "").strip() or None,
        "images": json.dumps(_split_list(row.get("images", "")), ensure_ascii=False) if row.get("images") else None,
        "source_url": row.get("source_url", "").strip() or None,
        "source_note": row.get("source_note", "").strip() or None,
        "manual_tags": _split_list(row.get("manual_tags", "")),
        "status": 1,
    }


def import_products(
    db: Session,
    rows: Sequence[Dict[str, str]],
    category_id: Optional[int] = None,
) -> Dict:
    if not rows:
        raise ValueError("导入文件中没有有效数据")

    category = category_id or infer_import_category(rows[0].keys())
    if not category or category not in CATEGORY_SPEC_FIELDS:
        raise ValueError("无法识别导入品类，请在请求中明确传入 category_id")

    existing_products = db.query(Product).filter(Product.category_id == category).all()
    errors: List[ImportErrorRow] = []
    created_cards: List[Dict] = []
    success_count = 0

    for index, row in enumerate(rows, start=2):
        row_errors = _validate_row(index, category, row, existing_products)
        if row_errors:
            errors.extend(row_errors)
            continue

        payload = _build_product_payload(category, row)
        product = Product(**payload)
        db.add(product)
        db.flush()
        existing_products.append(product)
        created_cards.append(serialize_product_card(product, 1.0, "通过 Excel 模板导入"))
        success_count += 1

    if success_count:
        db.commit()
    else:
        db.rollback()

    return {
        "category_id": category,
        "category_name": CATEGORY_NAME_BY_ID.get(category, ""),
        "success_count": success_count,
        "error_count": len(errors),
        "errors": [error.__dict__ for error in errors],
        "preview": created_cards[:5],
    }
