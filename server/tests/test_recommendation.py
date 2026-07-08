"""推荐引擎测试：硬过滤、评分维度、硬规则。"""
import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

from models.product import Product
from services.rag_pipeline import GuideConstraints
from services.recommendation import (
    _apply_hard_rules,
    _budget_fit,
    _spec_fit,
    _user_fit,
)


def _make_product(**kwargs):
    """构造测试用 Product 对象。"""
    defaults = {
        "category_id": 1,
        "name": "测试球拍",
        "brand": "TEST",
        "specs": {
            "weight_class": "4U",
            "balance": "even-balanced",
            "shaft_flex": "medium",
            "suitable_level": ["intermediate", "advanced"],
            "suitable_style": ["attack", "balanced"],
        },
        "price": 500,
    }
    defaults.update(kwargs)
    return Product(**defaults)


class TestHardRules:
    def test_beginner_rejects_stiff_shaft(self):
        product = _make_product(specs={"shaft_flex": "stiff"})
        constraints = GuideConstraints(level="beginner")
        assert _apply_hard_rules(product, constraints) is False

    def test_beginner_accepts_medium_shaft(self):
        product = _make_product(specs={"shaft_flex": "medium"})
        constraints = GuideConstraints(level="beginner")
        assert _apply_hard_rules(product, constraints) is True

    def test_knee_sensitive_rejects_low_cushion(self):
        product = _make_product(
            category_id=4,
            specs={"cushion_score": 7.0},
        )
        constraints = GuideConstraints(physical={"knee_sensitive": True})
        assert _apply_hard_rules(product, constraints) is False

    def test_knee_sensitive_accepts_high_cushion(self):
        product = _make_product(
            category_id=4,
            specs={"cushion_score": 9.0},
        )
        constraints = GuideConstraints(physical={"knee_sensitive": True})
        assert _apply_hard_rules(product, constraints) is True


class TestUserFit:
    def test_exact_level_match(self):
        product = _make_product(specs={"suitable_level": ["intermediate"]})
        constraints = GuideConstraints(level="intermediate")
        assert _user_fit(product, constraints) == 1.0

    def test_product_too_advanced_for_user(self):
        product = _make_product(specs={"suitable_level": ["advanced", "competitive"]})
        constraints = GuideConstraints(level="beginner")
        assert _user_fit(product, constraints) < 0.5

    def test_missing_level_field_neutral(self):
        product = _make_product(specs={})
        constraints = GuideConstraints(level="beginner")
        assert _user_fit(product, constraints) == 0.7


class TestBudgetFit:
    def test_well_within_budget(self):
        product = _make_product(price=400)
        constraints = GuideConstraints(budget_max=500)
        assert _budget_fit(product, constraints) == 1.0

    def test_at_budget_boundary(self):
        product = _make_product(price=475)
        constraints = GuideConstraints(budget_max=500)
        assert _budget_fit(product, constraints) == 0.75

    def test_over_budget(self):
        product = _make_product(price=600)
        constraints = GuideConstraints(budget_max=500)
        assert _budget_fit(product, constraints) == 0.0

    def test_no_budget_constraint(self):
        product = _make_product(price=999)
        constraints = GuideConstraints()
        assert _budget_fit(product, constraints) == 1.0


class TestSpecFit:
    def test_beginner_flexible_shaft_bonus(self):
        product = _make_product(specs={"shaft_flex": "flexible", "weight_class": "4U"})
        constraints = GuideConstraints(level="beginner")
        assert _spec_fit(product, constraints) >= 1.0

    def test_attack_style_head_heavy_bonus(self):
        product = _make_product(specs={"balance": "head-heavy"})
        constraints = GuideConstraints(style="attack")
        assert _spec_fit(product, constraints) >= 1.0

    def test_string_gauge_beginner_bonus(self):
        product = _make_product(
            category_id=2,
            specs={"gauge": "0.70"},
        )
        constraints = GuideConstraints(level="beginner")
        assert _spec_fit(product, constraints) >= 0.9

    def test_shuttle_material_advanced_bonus(self):
        product = _make_product(
            category_id=3,
            specs={"material": "goose_feather"},
        )
        constraints = GuideConstraints(level="advanced")
        assert _spec_fit(product, constraints) >= 0.95
