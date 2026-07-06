"""
购物车ORM模型
"""
from sqlalchemy import Column, Integer, DateTime, func

from database import Base


class Cart(Base):
    """购物车表模型"""

    __tablename__ = "t_cart"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="购物车ID")
    user_id = Column(Integer, nullable=False, comment="用户ID")
    product_id = Column(Integer, nullable=False, comment="装备ID")
    quantity = Column(Integer, default=1, comment="数量")
    checked = Column(Integer, default=1, comment="是否选中:1是0否")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
