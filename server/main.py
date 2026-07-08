"""FastAPI application entry."""
import json
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from bootstrap import init_database
from config import CORS_ORIGINS, PROJECT_NAME, UPLOAD_DIR
from database import SessionLocal
from routers import (
    admin_profile,
    admin_user,
    auth,
    banner,
    category,
    chat,
    dashboard,
    knowledge,
    product,
    upload,
    user_profile,
)
from utils.rate_limit import limiter


# ---------------------------------------------------------------------------
# 结构化日志（JSON），便于接入 ELK / Loki
# ---------------------------------------------------------------------------
class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


_logging_handler = logging.StreamHandler(sys.stdout)
_logging_handler.setFormatter(_JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[_logging_handler])
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application starting", extra={"project": PROJECT_NAME})
    init_database()
    yield
    logger.info("application shutting down")


app = FastAPI(
    title=PROJECT_NAME,
    description="羽毛球装备品类库与 RAG AI 选品系统后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter 绑定
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 限定具体源（不再 allow_origins=["*"]）
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(auth.router)
app.include_router(category.router)
app.include_router(product.router)
app.include_router(banner.router)
app.include_router(admin_user.router)
app.include_router(dashboard.router)
app.include_router(knowledge.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(admin_profile.router)
app.include_router(user_profile.router)


@app.get("/")
async def root():
    return {"message": PROJECT_NAME, "status": "running"}


@app.get("/api/health")
async def health():
    """深度健康检查：验证数据库连通性。"""
    checks: dict = {"status": "ok", "project": PROJECT_NAME}
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        checks["status"] = "degraded"
    finally:
        db.close()
    return checks


@app.get("/metrics")
async def metrics():
    """Prometheus 指标端点。"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
