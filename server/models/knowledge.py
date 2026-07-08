"""
知识库文件ORM模型
"""
from sqlalchemy import Column, Integer, String, DateTime, func

from database import Base


class KnowledgeFile(Base):
    """知识库文件表模型"""

    __tablename__ = "t_knowledge_file"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="知识库文件ID")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_type = Column(String(20), nullable=False, comment="文件类型")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    brand = Column(String(50), comment="品牌")
    series = Column(String(100), comment="系列")
    model_aliases = Column(String(500), comment="型号别名(逗号分隔)")
    doc_type = Column(String(30), comment="文档类型: compare/params/guide/knowledge")
    file_size = Column(Integer, default=0, comment="文件大小(字节)")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    status = Column(Integer, default=0, comment="状态:0待处理1已向量化2失败")
    error_msg = Column(String(500), comment="错误信息")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
