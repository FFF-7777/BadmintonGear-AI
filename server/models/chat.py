"""
AI聊天消息ORM模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func

from database import Base


class ChatMessage(Base):
    """AI聊天消息表模型"""

    __tablename__ = "t_chat_message"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="消息ID")
    user_id = Column(Integer, nullable=False, comment="用户ID")
    session_id = Column(String(64), nullable=False, comment="会话ID")
    role = Column(String(20), nullable=False, comment="角色:user/assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
