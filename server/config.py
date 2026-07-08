"""项目配置。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# override=True：强制以 .env 为准，覆盖进程继承的环境变量（uvicorn reloader
# 常驻主进程会把早期 .env 的 key 注入环境变量，若不开 override，改 .env 后
# reload worker 仍继承旧 key，导致子进程 chroma_runner 调 DashScope 时 401）。
load_dotenv(ROOT_DIR / ".env", override=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(BASE_DIR / 'dev.db').as_posix()}",
)

SECRET_KEY = os.getenv("SECRET_KEY", "badminton-rag-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "D:/uploads14"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

KNOWLEDGE_DIR = UPLOAD_DIR / "knowledge"
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

PRODUCT_DIR = UPLOAD_DIR / "product"
PRODUCT_DIR.mkdir(parents=True, exist_ok=True)

BANNER_DIR = UPLOAD_DIR / "banner"
BANNER_DIR.mkdir(parents=True, exist_ok=True)

AVATAR_DIR = UPLOAD_DIR / "avatar"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

CHROMA_DIR = BASE_DIR / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "badminton_rag_knowledge")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL",
    "https://llm-e7ls8vvabwv7yp9a4.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen3.6-plus")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "2048"))

RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
RAG_CANDIDATE_K = int(os.getenv("RAG_CANDIDATE_K", "12"))
RAG_RRF_K = int(os.getenv("RAG_RRF_K", "60"))
RAG_RELEVANCE_THRESHOLD = float(os.getenv("RAG_RELEVANCE_THRESHOLD", "0.15"))
RAG_HISTORY_TURNS = int(os.getenv("RAG_HISTORY_TURNS", "6"))
RAG_MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "6000"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

PROJECT_NAME = "羽智选 BadmintonGear AI"
