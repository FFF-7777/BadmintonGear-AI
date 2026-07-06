"""
装备分类ORM模型
"""
from sqlalchemy import Column, Integer, String, DateTime, func

from database import Base


class Category(Base):
    """装备分类表模型"""

    __tablename__ = "t_category"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name = Column(String(50), nullable=False, comment="分类名称")
    sort = Column(Integer, default=0, comment="排序")
    status = Column(Integer, default=1, comment="状态:1启用0禁用")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
