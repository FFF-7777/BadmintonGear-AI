"""
管理员ORM模型
"""
from sqlalchemy import Column, Integer, String, DateTime, func

from database import Base


class Admin(Base):
    """管理员表模型"""

    __tablename__ = "t_admin"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="管理员ID")
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password = Column(String(64), nullable=False, comment="密码(MD5)")
    nickname = Column(String(50), comment="昵称")
    avatar = Column(String(255), comment="头像")
    status = Column(Integer, default=1, comment="状态:1正常0禁用")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
