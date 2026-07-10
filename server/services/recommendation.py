"""
羽毛球装备推荐决策引擎（P0 新增）

职责：
1. 结构化商品检索路线（P0-2）：把用户约束翻译为对 t_product 的 SQL 硬过滤。
2. 可解释加权评分（P0-3）：UserFit / StyleFit / BudgetFit / SpecMatch。
3. 硬性过滤规则（P0-3）：新手不推超硬中杆、膝盖敏感优先缓震等。

设计原则（对齐架构文档第 19 节）：
- 推荐引擎只负责"筛选 + 排序 + 规则"，不负责生成自然语言。
- 商品参数只来自结构化商品库（t_product.specs），杜绝 LLM 编造。
- 输出可解释：每个候选都带评分与中文适配理由，供 Prompt 组装引用。
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence

from sqlalchemy.orm import Session

from config import ENABLED_RECOMMENDATION_CATEGORIES
from models.product import Product
from services.rag_pipeline import (
    CATEGORY_NAME_BY_ID,
    GuideConstraints,
    extract_compare_targets,
    extract_model_tokens,
    infer_brand,
    normalize_model_token,
    normalize_text,
)


# 水平有序映射，用于"商品要求高于用户水平"的判定
LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2, "competitive": 3}
LEVEL_CN = {"beginner": "新手", "intermediate": "进阶", "advanced": "高手", "competitive": "专业"}

# 评分权重：对齐新 RAG 改进清单，把来源可信度纳入排序。
_WEIGHTS = {
    "user_fit": 0.25,
    "style_fit": 0.20,
    "spec_fit": 0.20,
    "budget_fit": 0.15,
    "confidence_fit": 0.15,
    "availability_fit": 0.05,
}
_WEIGHT_SUM = sum(_WEIGHTS.values())
_CATEGORY_KEY_BY_ID = {1: "racket", 2: "string", 3: "shuttlecock", 4: "shoes"}
_ENABLED_CATEGORY_IDS = {
    category_id
    for category_id, key in _CATEGORY_KEY_BY_ID.items()
    if key in ENABLED_RECOMMENDATION_CATEGORIES
}

CONFIDENCE_SCORE_MAP = {
    "高": 1.0,
    "中高": 0.9,
    "中": 0.75,
    "中低": 0.45,
    "低": 0.2,
    "未知": 0.4,
}
_CONFIDENCE_ALIASES = {
    "high": "高",
    "medium_high": "中高",
    "mid_high": "中高",
    "medium": "中",
    "mid": "中",
    "medium_low": "中低",
    "mid_low": "中低",
    "low": "低",
    "unknown": "未知",
}
_RACKET_REQUIRED_FACTS = ("weight_class", "balance", "shaft_flex")
_UNVERIFIED_FIELD_KEYS = ("unverified_fields", "pending_verification_fields", "待核验字段")
_MODEL_SUFFIX_RE = re.compile(r"\d{1,4}[A-Z]{0,6}$")


# ---------------------------------------------------------------------------
# P0-2 结构化商品检索路线
# ---------------------------------------------------------------------------

def retrieve_candidates(db: Session, constraints: GuideConstraints) -> List[Product]:
    """按约束对商品库做硬过滤，返回候选商品列表。"""
    query = db.query(Product).filter(Product.status == 1)
    query = query.filter(Product.category_id.in_(_ENABLED_CATEGORY_IDS or {-1}))
    if constraints.category_ids:
        query = query.filter(Product.category_id.in_(constraints.category_ids))
    if constraints.budget_max is not None:
        query = query.filter(Product.price <= constraints.budget_max)
    if constraints.budget_min is not None:
        query = query.filter(Product.price >= constraints.budget_min)
    return query.all()


def _ensure_list(value) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def source_confidence_label(product: Product) -> str:
    """读取商品来源可信度；当前兼容放在 specs.source_confidence 的存量方案。"""
    specs = product.specs or {}
    raw = specs.get("source_confidence") or specs.get("confidence") or "未知"
    label = str(raw).strip()
    if not label:
        return "未知"
    normalized = label.lower().replace("-", "_").replace(" ", "_")
    return _CONFIDENCE_ALIASES.get(normalized, label)


def _confidence_fit(product: Product) -> float:
    return CONFIDENCE_SCORE_MAP.get(source_confidence_label(product), CONFIDENCE_SCORE_MAP["未知"])


def _unverified_fields(product: Product) -> List[str]:
    specs = product.specs or {}
    fields: List[str] = []
    for key in _UNVERIFIED_FIELD_KEYS:
        fields.extend(_ensure_list(specs.get(key)))
    return list(dict.fromkeys(fields))


def _has_minimum_primary_facts(product: Product) -> bool:
    if product.category_id != 1:
        return False
    specs = product.specs or {}
    return sum(1 for field in _RACKET_REQUIRED_FACTS if specs.get(field)) >= 2


def _is_primary_recommendation(product: Product) -> bool:
    return _confidence_fit(product) >= CONFIDENCE_SCORE_MAP["中"] and _has_minimum_primary_facts(product)


def _risk_notes(product: Product) -> List[str]:
    notes = ["参考价仅用于预算对比，不代表实时售价。"]
    source_confidence = source_confidence_label(product)
    if source_confidence in {"中低", "低", "未知"}:
        notes.append(f"来源可信度为“{source_confidence}”，购买前建议核验品牌官方页或正规零售商页面。")
    fields = _unverified_fields(product)
    if fields:
        notes.append("待核验字段：" + "、".join(fields))
    return notes


def recommendation_confidence(product: Product, constraints: GuideConstraints) -> str:
    """面向前端/LLM 的推荐置信度，不等同于来源可信度。"""
    source_score = _confidence_fit(product)
    user_info_score = sum(bool(value) for value in [
        constraints.level,
        constraints.style,
        constraints.play_type,
        constraints.budget_min is not None or constraints.budget_max is not None,
    ])
    if source_score >= 0.9 and user_info_score >= 2 and _has_minimum_primary_facts(product):
        return "高"
    if source_score >= 0.75 and _has_minimum_primary_facts(product):
        return "中高" if user_info_score >= 1 else "中"
    if source_score >= 0.45:
        return "中"
    return "低"


def derive_display_tags(product: Product) -> List[str]:
    """根据结构化字段推导展示标签。"""
    tags = _ensure_list(product.tags) + _ensure_list(product.manual_tags)
    specs = product.specs or {}
    if product.category_id == 1:
        if specs.get("balance") == "head-heavy":
            tags.append("进攻")
        if specs.get("balance") == "head-light":
            tags.append("速度")
        if specs.get("shaft_flex") in ("flexible", "medium"):
            tags.append("新手友好")
    elif product.category_id == 2:
        if specs.get("durability") in ("high", "very_high"):
            tags.append("耐打")
        if specs.get("repulsion") in ("high", "very_high"):
            tags.append("高弹")
    elif product.category_id == 3:
        if specs.get("material") == "goose_feather":
            tags.append("飞行稳定")
        if specs.get("usage_scene"):
            tags.append(str(specs["usage_scene"]))
    elif product.category_id == 4:
        if float(specs.get("cushion_score", 0) or 0) >= 8.5:
            tags.append("高缓震")
        if specs.get("width_fit") in ("wide", "wide-friendly"):
            tags.append("宽脚友好")
    return list(dict.fromkeys(tag for tag in tags if tag))


def serialize_product_card(product: Product, score: float, reason: str) -> Dict:
    source_confidence = source_confidence_label(product)
    confidence = recommendation_confidence(product, GuideConstraints())
    return {
        "id": product.id,
        "name": product.name,
        "brand": product.brand or (product.specs or {}).get("brand", ""),
        "series": product.series or "",
        "price": float(product.price),
        "image": product.image or "",
        "category_id": product.category_id,
        "category_name": CATEGORY_NAME_BY_ID.get(product.category_id, ""),
        "score": round(score, 3),
        "reason": reason,
        "source_confidence": source_confidence,
        "confidence": confidence,
        "recommendation_role": "primary" if _is_primary_recommendation(product) else "backup",
        "risk": _risk_notes(product),
        "specs": product.specs or {},
        "tags": derive_display_tags(product),
        "manual_tags": _ensure_list(product.manual_tags),
    }


def _product_match_keys(product: Product) -> set:
    parts = [
        product.name,
        product.brand or "",
        product.series or "",
        " ".join(_ensure_list(product.model_aliases)),
    ]
    keys = {
        normalize_model_token(part)
        for part in parts
        if normalize_model_token(part)
    }
    for part in parts:
        for token in extract_model_tokens(part):
            keys.add(normalize_model_token(token))
    return {key for key in keys if key}


def _model_suffix(token: str) -> str:
    match = _MODEL_SUFFIX_RE.search(normalize_model_token(token))
    return match.group(0) if match else ""


def _product_match_score(product: Product, query_text: str) -> tuple:
    normalized_query = normalize_text(query_text)
    query_key = normalize_model_token(normalized_query)
    query_tokens = {normalize_model_token(token) for token in extract_model_tokens(normalized_query)}
    query_suffixes = {_model_suffix(token) for token in query_tokens}
    query_suffixes.discard("")
    product_keys = _product_match_keys(product)
    product_suffixes = {_model_suffix(key) for key in product_keys}
    product_suffixes.discard("")
    haystack = normalize_model_token(" ".join(filter(None, [
        product.name,
        product.brand or "",
        product.series or "",
        " ".join(_ensure_list(product.model_aliases)),
    ])))

    overlap = query_tokens & product_keys
    score = 0.0
    reasons: List[str] = []
    if overlap:
        score += 1.2
        reasons.append("型号别名精确命中：" + ", ".join(sorted(overlap)))
    if any(key and key in query_key for key in product_keys if len(key) >= 4):
        score += 1.0
        reasons.append("商品名/别名出现在问题中")
    if query_key and query_key in haystack:
        score += 0.7
        reasons.append("问题文本直接命中商品信息")

    suffix_overlap = query_suffixes & product_suffixes
    inferred_brand = infer_brand(normalized_query)
    brand_hit = bool(
        product.brand
        and (
            product.brand.upper() in normalized_query.upper()
            or (inferred_brand and inferred_brand.upper() == product.brand.upper())
        )
    )
    series_hit = bool(product.series and normalize_model_token(product.series) in query_key)
    if suffix_overlap and (brand_hit or series_hit):
        score += 0.65
        reasons.append("品牌/系列 + 数字型号命中：" + ", ".join(sorted(suffix_overlap)))

    return score, "；".join(dict.fromkeys(reasons)) if reasons else ""


def match_products_for_query(
    db: Session,
    query_text: str,
    limit: int = 4,
) -> List[Dict]:
    """按型号/系列/别名直连结构化商品库，优先服务具体型号与对比类问题。"""
    normalized_query = normalize_text(query_text)
    if not normalized_query:
        return []
    query_tokens = {normalize_model_token(token) for token in extract_model_tokens(normalized_query)}
    if not query_tokens and len(normalized_query) < 2:
        return []

    products = [
        product
        for product in db.query(Product).filter(Product.status == 1).all()
        if product.category_id in _ENABLED_CATEGORY_IDS
    ]
    candidates: List[Dict] = []
    product_by_id = {}
    for product in products:
        if product.category_id not in _ENABLED_CATEGORY_IDS:
            continue
        score, reason = _product_match_score(product, query_text)
        if score > 0:
            card = serialize_product_card(product, score, reason)
            candidates.append(card)
            product_by_id[card["id"]] = product

    candidates.sort(key=lambda item: item["score"], reverse=True)
    targets = extract_compare_targets(query_text)
    if len(targets) >= 2:
        selected: List[Dict] = []
        selected_ids = set()
        for target in targets[:2]:
            target_candidates = []
            for item in candidates:
                product = product_by_id.get(item["id"])
                if not product:
                    continue
                score, _ = _product_match_score(product, target)
                if score > 0:
                    target_candidates.append((score, item))
            target_candidates.sort(key=lambda pair: pair[0], reverse=True)
            if target_candidates:
                item = target_candidates[0][1]
                if item["id"] not in selected_ids:
                    selected.append(item)
                    selected_ids.add(item["id"])
        selected.extend(item for item in candidates if item["id"] not in selected_ids)
        return selected[:limit]
    return candidates[:limit]


# ---------------------------------------------------------------------------
# P0-3 评分维度
# ---------------------------------------------------------------------------

def _user_fit(product: Product, constraints: GuideConstraints) -> float:
    """用户水平与商品适用水平的匹配度。"""
    specs = product.specs or {}
    levels = specs.get("suitable_level") or []
    if not levels:
        return 0.7  # 缺字段 → 中立
    if constraints.level:
        if constraints.level in levels:
            return 1.0
        user_lv = LEVEL_ORDER.get(constraints.level, 1)
        min_prod_lv = min(LEVEL_ORDER.get(lv, 1) for lv in levels)
        if min_prod_lv > user_lv:
            return 0.3  # 商品要求高于用户水平，不匹配
        return 0.8
    return 0.8


def _style_fit(product: Product, constraints: GuideConstraints) -> float:
    """打法匹配度。"""
    specs = product.specs or {}
    styles = specs.get("suitable_style") or []
    if not styles or not constraints.style:
        return 0.8
    return 1.0 if constraints.style in styles else 0.5


def _budget_fit(product: Product, constraints: GuideConstraints) -> float:
    """预算匹配度（候选已按 budget_max 预过滤，这里在预算内给更便宜者更高分）。"""
    if constraints.budget_max is None:
        return 1.0
    price = float(product.price)
    if price <= 0:
        return 1.0
    ratio = price / constraints.budget_max
    if ratio <= 0.85:
        return 1.0
    if ratio <= 1.0:
        return 0.75
    return 0.0


def _availability_fit(product: Product) -> float:
    return 1.0 if product.status == 1 else 0.0


def _spec_fit(product: Product, constraints: GuideConstraints) -> float:
    """基于规格的软性适配（细分参数加分）。覆盖全部 4 个品类。"""
    specs = product.specs or {}
    score = 0.8
    if product.category_id == 1:  # 球拍
        weight_class = specs.get("weight_class")
        shaft = specs.get("shaft_flex")
        balance = specs.get("balance")
        if constraints.level == "beginner" and weight_class in ("4U", "5U"):
            score = max(score, 1.0)
        if constraints.level == "beginner" and shaft in ("flexible", "medium"):
            score = max(score, 1.0)
        if constraints.style == "attack" and balance == "head-heavy":
            score = max(score, 1.0)
    elif product.category_id == 4:  # 球鞋
        if constraints.physical.get("knee_sensitive"):
            cushion = specs.get("cushion_score", 0)
            if cushion >= 9.0:
                score = 1.0
            elif cushion >= 8.0:
                score = max(score, 0.9)
    elif product.category_id == 2:  # 球线（P2d：原仅球拍/球鞋有效，现补软性适配）
        gauge = specs.get("gauge")
        if gauge is not None:
            try:
                gauge_f = float(gauge)
            except (TypeError, ValueError):
                gauge_f = None
            if gauge_f is not None:
                # 新手更耐打优先 → 较粗线（>=0.68mm）加分
                if constraints.level == "beginner" and gauge_f >= 0.68:
                    score = max(score, 0.9)
                # 控球/拉吊打法 → 细线（<=0.66mm）手感更好
                if constraints.style == "control" and gauge_f <= 0.66:
                    score = max(score, 0.9)
    elif product.category_id == 3:  # 羽毛球（P2d）
        material = specs.get("material")
        if constraints.level == "beginner" and material == "duck_feather":
            score = max(score, 0.9)  # 新手性价比优先，鸭毛更实惠
        if constraints.level in ("advanced", "competitive") and material == "goose_feather":
            score = max(score, 0.95)  # 高频训练/比赛更稳定耐打
    return score


def _apply_hard_rules(product: Product, constraints: GuideConstraints) -> bool:
    """硬性过滤：返回 False 表示应排除该商品。"""
    specs = product.specs or {}

    # 新手不推超硬/硬中杆球拍
    if product.category_id == 1 and constraints.level == "beginner":
        if specs.get("shaft_flex") in ("stiff", "extra-stiff"):
            return False

    # 膝盖敏感不推低缓震球鞋
    if product.category_id == 4 and constraints.physical.get("knee_sensitive"):
        if specs.get("cushion_score", 99) < 8.0:
            return False

    # 脚踝敏感不推低支撑球鞋
    if product.category_id == 4 and constraints.physical.get("ankle_sensitive"):
        if specs.get("ankle_support") == "low":
            return False

    # 双打防守型不推极端头重 3U 拍
    if (
        product.category_id == 1
        and constraints.style == "defense"
        and constraints.play_type in ("doubles", "mixed")
        and specs.get("balance") == "head-heavy"
        and specs.get("weight_class") == "3U"
    ):
        return False

    return True


# ---------------------------------------------------------------------------
# 理由生成（可解释）
# ---------------------------------------------------------------------------

_BALANCE_CN = {"head-heavy": "头重进攻", "even-balanced": "平衡均衡", "head-light": "头轻灵活"}
_SHAFT_CN = {"flexible": "中软杆易上手", "medium": "中杆适中", "stiff": "中硬杆", "extra-stiff": "高硬杆"}
_MATERIAL_CN = {"goose_feather": "鹅毛稳定耐打", "duck_feather": "鸭毛性价比高"}


def _build_reason(product: Product, constraints: GuideConstraints) -> str:
    parts: List[str] = []
    specs = product.specs or {}

    if product.category_id == 1:
        wc = specs.get("weight_class")
        if wc:
            parts.append(f"{wc}重量")
        bal = specs.get("balance")
        if bal:
            parts.append(_BALANCE_CN.get(bal, bal))
        shaft = specs.get("shaft_flex")
        if shaft:
            parts.append(_SHAFT_CN.get(shaft, shaft))
    elif product.category_id == 4:
        cs = specs.get("cushion_score")
        ss = specs.get("support_score")
        if cs:
            parts.append(f"缓震{cs}")
        if ss:
            parts.append(f"支撑{ss}")
    elif product.category_id == 3:
        mat = specs.get("material")
        if mat:
            parts.append(_MATERIAL_CN.get(mat, mat))
        sp = specs.get("speed")
        if sp:
            parts.append(f"{sp}速")
    elif product.category_id == 2:
        ga = specs.get("gauge")
        if ga:
            parts.append(f"线径{ga}")

    if constraints.budget_max is not None and float(product.price) <= constraints.budget_max:
        parts.append("价格在区间内")
    if constraints.level and constraints.level in (specs.get("suitable_level") or []):
        parts.append(f"适合{LEVEL_CN.get(constraints.level, '')}")
    if constraints.physical.get("knee_sensitive") and product.category_id == 4:
        parts.append("缓震优先保护膝盖")

    return "；".join(parts) if parts else "综合参数匹配度较高"


# ---------------------------------------------------------------------------
# 排序入口
# ---------------------------------------------------------------------------

def score_and_rank(
    db: Session,
    constraints: GuideConstraints,
    intent: str = "single_recommend",
    top_n: int = 5,
) -> List[Dict]:
    """返回排序后的推荐商品列表（含评分与理由）。"""
    candidates = retrieve_candidates(db, constraints)
    ranked: List[Dict] = []

    for product in candidates:
        if not _apply_hard_rules(product, constraints):
            continue
        user_fit = _user_fit(product, constraints)
        style_fit = _style_fit(product, constraints)
        budget_fit = _budget_fit(product, constraints)
        spec_fit = _spec_fit(product, constraints)
        confidence_fit = _confidence_fit(product)
        availability_fit = _availability_fit(product)
        final = (
            _WEIGHTS["user_fit"] * user_fit
            + _WEIGHTS["style_fit"] * style_fit
            + _WEIGHTS["spec_fit"] * spec_fit
            + _WEIGHTS["budget_fit"] * budget_fit
            + _WEIGHTS["confidence_fit"] * confidence_fit
            + _WEIGHTS["availability_fit"] * availability_fit
        ) / _WEIGHT_SUM

        card = serialize_product_card(product, final, _build_reason(product, constraints))
        card["confidence"] = recommendation_confidence(product, constraints)
        ranked.append(card)

    ranked.sort(
        key=lambda item: (
            1 if item.get("recommendation_role") == "primary" else 0,
            item["score"],
        ),
        reverse=True,
    )
    # 组合推荐：每个品类最多保留 2 个，避免单品类霸榜
    if intent == "bundle_recommend":
        per_cat: Dict[int, int] = {}
        diversified: List[Dict] = []
        for item in ranked:
            cid = item["category_id"]
            per_cat[cid] = per_cat.get(cid, 0) + 1
            if per_cat[cid] <= 2:
                diversified.append(item)
        ranked = diversified[:top_n]
    return ranked[:top_n]


def recommend_products(
    db: Session,
    constraints: GuideConstraints,
    intent: str = "single_recommend",
    top_n: int = 5,
) -> List[Dict]:
    """对外统一入口：约束 → 推荐商品卡列表。"""
    return score_and_rank(db, constraints, intent=intent, top_n=top_n)
