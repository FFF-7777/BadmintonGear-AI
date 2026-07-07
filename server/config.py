"""
项目配置文件
基于LangChain的羽毛球装备智能导购小程序

从项目根目录的 .env 文件加载敏感配置，可通过环境变量覆盖。
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录（server/ 的上一级）
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# 加载 .env 文件（项目根目录）
load_dotenv(ROOT_DIR / ".env")

# ---------- 数据库配置 ----------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:123456@127.0.0.1:3308/db_ai_shop?charset=utf8mb4",
)

# ---------- JWT 配置 ----------
SECRET_KEY = os.getenv("SECRET_KEY", "ai-shop-secret-key-2026-langchain-rag")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# ---------- 文件上传目录 ----------
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "D:/uploads14"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 知识库文件子目录
KNOWLEDGE_DIR = UPLOAD_DIR / "knowledge"
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

# 装备图片子目录
PRODUCT_DIR = UPLOAD_DIR / "product"
PRODUCT_DIR.mkdir(parents=True, exist_ok=True)

# 轮播图子目录
BANNER_DIR = UPLOAD_DIR / "banner"
BANNER_DIR.mkdir(parents=True, exist_ok=True)

# 头像子目录
AVATAR_DIR = UPLOAD_DIR / "avatar"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Chroma 向量数据库 ----------
CHROMA_DIR = BASE_DIR / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "ai_shop_knowledge")

# ---------- OpenAI 兼容接口配置 ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL",
    "https://llm-e7ls8vvabwv7yp9a4.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen3.6-plus")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "2048"))

# ---------- RAG 检索参数 ----------
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
RAG_CANDIDATE_K = int(os.getenv("RAG_CANDIDATE_K", "12"))
RAG_RRF_K = int(os.getenv("RAG_RRF_K", "60"))
RAG_RELEVANCE_THRESHOLD = float(os.getenv("RAG_RELEVANCE_THRESHOLD", "0.15"))
RAG_HISTORY_TURNS = int(os.getenv("RAG_HISTORY_TURNS", "6"))
RAG_MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "6000"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# ---------- 项目名称 ----------
PROJECT_NAME = "基于LangChain的羽毛球装备智能导购小程序"
