"""
用户羽毛球画像 ORM 模型（P1-4 跨会话持久化）。

仅新增独立表 t_user_profile，不改动任何现有表/列，也不触碰知识库向量库(chroma)。
用于把用户水平/打法/预算/身体情况等偏好在多次会话间记住，实现跨会话个性化推荐。
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, func

from database import Base


class UserProfile(Base):
    """用户羽毛球画像：水平/打法/预算/身体情况，跨会话持久化。"""

    __tablename__ = "t_user_profile"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(Integer, unique=True, nullable=False, index=True, comment="关联 t_user.id")
    level = Column(String(30), comment="水平: beginner/intermediate/advanced/competitive")
    style = Column(String(30), comment="打法: attack/defense/control/balanced")
    play_type = Column(String(20), comment="单双打: singles/doubles/mixed")
    budget_min = Column(Float, comment="预算下限(元)")
    budget_max = Column(Float, comment="预算上限(元)")
    # 身体情况以逗号拼接的键存储，如 "knee_sensitive,ankle_sensitive"；空为 None
    physical = Column(String(100), comment="身体情况键列表(逗号分隔)")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
