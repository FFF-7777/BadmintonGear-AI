"""
跨会话用户画像（P1-4）离线自检。

不触碰 chroma 向量库、不调用 LLM；仅在内存 SQLite 上验证：
- _merge_profile_into：本次约束优先、画像补缺、身体情况取并集
- _persist_profile / _load_profile_constraints：持久化、跨轮合并、空约束不写
- _format_profile_text：画像转中文提示
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from services.ai_service import AIService, GuideConstraints


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_merge_profile_into_base_priority_and_fill():
    base = GuideConstraints(level="advanced")
    profile = GuideConstraints(level="beginner", style="control", budget_max=500.0)
    merged = AIService._merge_profile_into(base, profile)
    # 本次明确说出的优先
    assert merged.level == "advanced"
    # 画像补缺未提及字段
    assert merged.style == "control"
    assert merged.budget_max == 500.0
    # 不修改入参
    assert base.style is None
    assert profile.level == "beginner"


def test_merge_profile_into_physical_union():
    base = GuideConstraints(physical={"wrist_sensitive": True})
    profile = GuideConstraints(physical={"knee_sensitive": True})
    merged = AIService._merge_profile_into(base, profile)
    assert set(merged.physical.keys()) == {"wrist_sensitive", "knee_sensitive"}
    # 同名键以本次为准
    base2 = GuideConstraints(physical={"knee_sensitive": True})
    profile2 = GuideConstraints(physical={"knee_sensitive": True})
    merged2 = AIService._merge_profile_into(base2, profile2)
    assert merged2.physical == {"knee_sensitive": True}


def test_merge_profile_into_none_profile_passthrough():
    base = GuideConstraints(level="beginner", budget_max=300.0)
    merged = AIService._merge_profile_into(base, None)
    assert merged.level == "beginner"
    assert merged.budget_max == 300.0


def test_persist_and_load_round_trip():
    db = _make_session()
    try:
        # 第一轮：新手 + 预算上限 500
        fresh1 = GuideConstraints(level="beginner", budget_max=500.0)
        AIService._persist_profile(db, user_id=1, fresh=fresh1)
        loaded = AIService._load_profile_constraints(db, user_id=1)
        assert loaded.level == "beginner"
        assert loaded.budget_max == 500.0
        assert loaded.style is None

        # 第二轮：进阶打法(进攻) + 预算上调到 800（应覆盖旧值），身体情况并集
        fresh2 = GuideConstraints(style="attack", budget_max=800.0, physical={"knee_sensitive": True})
        AIService._persist_profile(db, user_id=1, fresh=fresh2)
        loaded2 = AIService._load_profile_constraints(db, user_id=1)
        # 历史字段保留
        assert loaded2.level == "beginner"
        # 本轮字段写入/覆盖
        assert loaded2.style == "attack"
        assert loaded2.budget_max == 800.0
        assert loaded2.physical == {"knee_sensitive": True}

        # 第三轮：只补充身体情况（脚踝敏感），不应清空已有字段
        fresh3 = GuideConstraints(physical={"ankle_sensitive": True})
        AIService._persist_profile(db, user_id=1, fresh=fresh3)
        loaded3 = AIService._load_profile_constraints(db, user_id=1)
        assert loaded3.level == "beginner"
        assert loaded3.style == "attack"
        assert loaded3.budget_max == 800.0
        assert set(loaded3.physical.keys()) == {"knee_sensitive", "ankle_sensitive"}
    finally:
        db.close()


def test_persist_empty_constraints_no_write():
    db = _make_session()
    try:
        empty = GuideConstraints()
        AIService._persist_profile(db, user_id=99, fresh=empty)
        assert AIService._load_profile_constraints(db, user_id=99) is None
    finally:
        db.close()


def test_format_profile_text():
    c = GuideConstraints(
        level="beginner", style="control", play_type="doubles",
        budget_min=200.0, budget_max=600.0, physical={"knee_sensitive": True},
    )
    text = AIService._format_profile_text(c)
    assert text is not None
    assert "新手" in text
    assert "控制型" in text
    assert "双打" in text
    assert "200-600" in text or "200" in text
    assert "膝盖敏感" in text

    # 空约束返回 None
    assert AIService._format_profile_text(GuideConstraints()) is None
    assert AIService._format_profile_text(None) is None
