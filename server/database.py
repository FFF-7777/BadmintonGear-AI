"""
数据库连接模块
提供SQLAlchemy引擎和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DATABASE_URL

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明式基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话(依赖注入用)
    使用完毕后自动关闭连接
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
