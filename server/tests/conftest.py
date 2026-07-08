"""Pytest 共享 fixture：sys.path 注入 + TestClient + DB 会话。"""
import os
import sys
from pathlib import Path

# 测试环境默认 SECRET_KEY（防止 config.py 启动报错；生产环境必须由 .env 提供）
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

# 把 server/ 加入 sys.path，让测试能 import server 内部模块
SERVER_DIR = Path(__file__).resolve().parent.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app():
    """创建 FastAPI app 实例（不触发 lifespan 初始化）。"""
    from main import app
    return app


@pytest.fixture(scope="session")
def client(app):
    """FastAPI TestClient，用于 API 层测试。"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    """数据库会话 fixture。"""
    from database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
