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

# ---- 安全配置 ----
# SECRET_KEY 必须由环境变量提供，无默认值——启动时缺失即报错，防止公开仓库后伪造 token
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY 未配置。请在项目根 .env 中设置一个随机字符串，例如：\n"
        '  SECRET_KEY=$(python -c "import secrets;print(secrets.token_hex(32))")'
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# CORS 允许的源，逗号分隔；默认仅允许本地前端开发端口
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:5173,http://localhost:5174").split(",")
    if origin.strip()
]

# 种子管理员初始密码（首次创建时使用）；生产环境务必修改
ADMIN_INIT_PASSWORD = os.getenv("ADMIN_INIT_PASSWORD", "admin")

# ---- 文件上传目录（跨平台相对路径）----
# 默认放在项目同级目录，避免硬编码 Windows 绝对路径
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(ROOT_DIR / "uploads14")))
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
    "https://llm-e7ls8vvabw7yp9a4.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)
# 默认值与 .env 保持一致，避免混淆
CHAT_MODEL = os.getenv("CHAT_MODEL", "glm-5.1")
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

# ---- 接口限制 ----
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "1000"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))

# ---- Rate Limiting ----
RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "10/minute")
RATE_LIMIT_REGISTER = os.getenv("RATE_LIMIT_REGISTER", "5/minute")
RATE_LIMIT_CHAT = os.getenv("RATE_LIMIT_CHAT", "30/minute")

PROJECT_NAME = "羽智选 BadmintonGear AI"
