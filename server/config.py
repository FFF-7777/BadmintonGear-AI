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
    for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:5183,http://127.0.0.1:5184,http://localhost:5183,http://localhost:5184").split(",")
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
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen3.7-plus")
CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0.2"))
CHAT_TOP_P = float(os.getenv("CHAT_TOP_P", "0.85"))
CHAT_MAX_TOKENS = int(os.getenv("CHAT_MAX_TOKENS", "1200"))
CHAT_FREQUENCY_PENALTY = float(os.getenv("CHAT_FREQUENCY_PENALTY", "0.1"))
CHAT_PRESENCE_PENALTY = float(os.getenv("CHAT_PRESENCE_PENALTY", "0"))
ENABLE_THINKING = os.getenv("ENABLE_THINKING", "false").lower() in {"true", "1", "yes", "on"}
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "2048"))

# ---- Cross-Encoder 语义重排（P0-1，复用 DashScope qwen3-rerank）----
# gte-rerank 已于 2026-05-30 下线，官方推荐 qwen3-rerank。
# 重排只在主进程 safe_search 内对"已召回候选"做二次排序，不在 chroma 子进程内，
# 因此重排接口故障只退回启发式排序，绝不连累向量检索降级成空结果。
RERANK_ENABLED = os.getenv("RERANK_ENABLED", "true").lower() in {"true", "1", "yes", "on"}
RERANK_MODEL = os.getenv("RERANK_MODEL", "qwen3-rerank")
# 单次重排超时（秒）；超时/异常立即退回启发式，避免拖慢问答端点。
RERANK_TIMEOUT = float(os.getenv("RERANK_TIMEOUT", "8"))
# 原生 rerank 端点；留空则按 OPENAI_BASE_URL 推导（compatible-mode -> api/v1/services/rerank/...）。
RERANK_BASE_URL = os.getenv("RERANK_BASE_URL", "").strip()

RAG_TOP_K = int(os.getenv("RAG_TOP_K", "6"))
RAG_CANDIDATE_K = int(os.getenv("RAG_CANDIDATE_K", "30"))
RAG_RRF_K = int(os.getenv("RAG_RRF_K", "60"))
RAG_RELEVANCE_THRESHOLD = float(os.getenv("RAG_RELEVANCE_THRESHOLD", "0.15"))
RAG_HISTORY_TURNS = int(os.getenv("RAG_HISTORY_TURNS", "6"))
RAG_MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "9000"))
QUERY_REWRITE_ENABLED = os.getenv("QUERY_REWRITE_ENABLED", "true").lower() in {"true", "1", "yes", "on"}
QUERY_REWRITE_MAX_CHARS = int(os.getenv("QUERY_REWRITE_MAX_CHARS", "300"))
QUERY_REWRITE_TEMPERATURE = float(os.getenv("QUERY_REWRITE_TEMPERATURE", "0.1"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
MIN_CHUNK_CHARS = int(os.getenv("MIN_CHUNK_CHARS", "180"))
MAX_CHUNK_CHARS = int(os.getenv("MAX_CHUNK_CHARS", "1400"))
SPLIT_BY_HEADING = os.getenv("SPLIT_BY_HEADING", "true").lower() in {"true", "1", "yes", "on"}
KEEP_TABLES = os.getenv("KEEP_TABLES", "true").lower() in {"true", "1", "yes", "on"}
KEEP_YAML_BLOCKS = os.getenv("KEEP_YAML_BLOCKS", "true").lower() in {"true", "1", "yes", "on"}
PRODUCT_CHUNK_MODE = os.getenv("PRODUCT_CHUNK_MODE", "one_product_one_chunk")
ENABLED_RECOMMENDATION_CATEGORIES = tuple(
    item.strip()
    for item in os.getenv("ENABLED_RECOMMENDATION_CATEGORIES", "racket").split(",")
    if item.strip()
)
DISABLED_DETAIL_CATEGORIES = tuple(
    item.strip()
    for item in os.getenv("DISABLED_DETAIL_CATEGORIES", "string,shoes,shuttlecock").split(",")
    if item.strip()
)

# ---- 接口限制 ----
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "1000"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))

# ---- Rate Limiting ----
RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "10/minute")
RATE_LIMIT_REGISTER = os.getenv("RATE_LIMIT_REGISTER", "5/minute")
RATE_LIMIT_CHAT = os.getenv("RATE_LIMIT_CHAT", "30/minute")

PROJECT_NAME = "羽智选 BadmintonGear AI"
