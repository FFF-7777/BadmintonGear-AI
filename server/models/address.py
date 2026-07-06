"""
收货地址ORM模型
"""
from sqlalchemy import Column, Integer, String, DateTime, func

from database import Base


class Address(Base):
    """收货地址表模型"""

    __tablename__ = "t_address"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="地址ID")
    user_id = Column(Integer, nullable=False, comment="用户ID")
    name = Column(String(50), nullable=False, comment="收货人")
    phone = Column(String(20), nullable=False, comment="联系电话")
    address = Column(String(255), nullable=False, comment="详细地址")
    is_default = Column(Integer, default=0, comment="是否默认:1是0否")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
