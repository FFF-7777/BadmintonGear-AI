"""
订单ORM模型
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, func

from database import Base


class Order(Base):
    """订单表模型"""

    __tablename__ = "t_order"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="订单ID")
    order_no = Column(String(32), unique=True, nullable=False, comment="订单编号")
    user_id = Column(Integer, nullable=False, comment="用户ID")
    total_amount = Column(Numeric(10, 2), nullable=False, comment="订单总金额")
    pay_amount = Column(Numeric(10, 2), nullable=False, comment="实付金额")
    status = Column(Integer, default=0, comment="状态:0待支付1已支付2已发货3已完成4已取消")
    receiver_name = Column(String(50), comment="收货人")
    receiver_phone = Column(String(20), comment="收货电话")
    receiver_address = Column(String(255), comment="收货地址")
    remark = Column(String(255), comment="备注")
    pay_time = Column(DateTime, comment="支付时间")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class OrderItem(Base):
    """订单明细表模型"""

    __tablename__ = "t_order_item"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="订单明细ID")
    order_id = Column(Integer, nullable=False, comment="订单ID")
    product_id = Column(Integer, nullable=False, comment="装备ID")
    product_name = Column(String(100), nullable=False, comment="装备名称")
    product_image = Column(String(255), comment="装备图片")
    price = Column(Numeric(10, 2), nullable=False, comment="单价")
    quantity = Column(Integer, nullable=False, comment="数量")
    total_price = Column(Numeric(10, 2), nullable=False, comment="小计")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
