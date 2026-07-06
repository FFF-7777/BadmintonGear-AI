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
from services.rag_pipeline import GuideConstraints, CATEGORY_NAME_BY_ID


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
    """基于规格的软性适配（细分参数加分）。"""
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
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "category_id": product.category_id,
            "category_name": CATEGORY_NAME_BY_ID.get(product.category_id, ""),
            "score": round(final, 3),
            "reason": _build_reason(product, constraints),
            "specs": product.specs or {},
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
