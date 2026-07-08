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

from typing import Dict, List, Optional, Sequence

from sqlalchemy.orm import Session

from models.product import Product
from services.rag_pipeline import (
    CATEGORY_NAME_BY_ID,
    GuideConstraints,
    extract_model_tokens,
    normalize_model_token,
    normalize_text,
)


# 水平有序映射，用于"商品要求高于用户水平"的判定
LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2, "competitive": 3}
LEVEL_CN = {"beginner": "新手", "intermediate": "进阶", "advanced": "高手", "competitive": "专业"}

# 评分权重（仅使用可获取的 4 个维度，归一化后求和=1）
_WEIGHTS = {"user_fit": 0.25, "style_fit": 0.20, "budget_fit": 0.15, "spec_fit": 0.15}
_WEIGHT_SUM = sum(_WEIGHTS.values())


# ---------------------------------------------------------------------------
# P0-2 结构化商品检索路线
# ---------------------------------------------------------------------------

def retrieve_candidates(db: Session, constraints: GuideConstraints) -> List[Product]:
    """按约束对商品库做硬过滤，返回候选商品列表。"""
    query = db.query(Product).filter(Product.status == 1)
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
        "specs": product.specs or {},
        "tags": derive_display_tags(product),
        "manual_tags": _ensure_list(product.manual_tags),
    }


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

    candidates: List[Dict] = []
    for product in db.query(Product).filter(Product.status == 1).all():
        name_tokens = {normalize_model_token(token) for token in extract_model_tokens(product.name)}
        alias_tokens = {normalize_model_token(token) for token in _ensure_list(product.model_aliases)}
        pool = {
            normalize_model_token(product.name),
            normalize_model_token(product.series or ""),
            normalize_model_token(product.brand or ""),
            *name_tokens,
            *alias_tokens,
        }
        overlap = query_tokens & pool if query_tokens else set()
        haystack = normalize_text(" ".join(filter(None, [
            product.name,
            product.brand or "",
            product.series or "",
            " ".join(_ensure_list(product.model_aliases)),
        ]))).lower()

        score = 0.0
        if overlap:
            score += 1.0
        if normalized_query.lower() in haystack:
            score += 0.7
        if score > 0:
            reason = "型号或系列名直接命中"
            if overlap:
                reason = f"识别到型号别名：{', '.join(sorted(overlap))}"
            candidates.append(serialize_product_card(product, score, reason))

    candidates.sort(key=lambda item: item["score"], reverse=True)
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
        final = (
            _WEIGHTS["user_fit"] * user_fit
            + _WEIGHTS["style_fit"] * style_fit
            + _WEIGHTS["budget_fit"] * budget_fit
            + _WEIGHTS["spec_fit"] * spec_fit
        ) / _WEIGHT_SUM

        ranked.append({
            **serialize_product_card(product, final, _build_reason(product, constraints)),
        })

    ranked.sort(key=lambda item: item["score"], reverse=True)
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
