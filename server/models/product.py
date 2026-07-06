"""
装备ORM模型
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, func, JSON

from database import Base


class Product(Base):
    """装备表模型"""

    __tablename__ = "t_product"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="装备ID")
    category_id = Column(Integer, nullable=False, comment="分类ID")
    name = Column(String(100), nullable=False, comment="装备名称")
    description = Column(Text, comment="装备描述")
    specs = Column(JSON, comment="结构化规格(JSON):球拍/球线/羽毛球/球鞋各自参数")
    price = Column(Numeric(10, 2), nullable=False, comment="装备价格")
    stock = Column(Integer, default=0, comment="库存")
    image = Column(String(255), comment="装备主图")
    images = Column(Text, comment="装备图片(JSON数组)")
    sales = Column(Integer, default=0, comment="销量")
    status = Column(Integer, default=1, comment="状态:1上架0下架")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
