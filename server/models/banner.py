"""
轮播图ORM模型
"""
from sqlalchemy import Column, Integer, String, DateTime, func

from database import Base


class Banner(Base):
    """轮播图表模型"""

    __tablename__ = "t_banner"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="轮播图ID")
    title = Column(String(100), comment="标题")
    image = Column(String(255), nullable=False, comment="图片地址")
    link_type = Column(Integer, default=0, comment="链接类型:0无1装备2分类")
    link_id = Column(Integer, default=0, comment="链接ID")
    sort = Column(Integer, default=0, comment="排序")
    status = Column(Integer, default=1, comment="状态:1启用0禁用")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
