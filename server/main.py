"""FastAPI application entry."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from bootstrap import init_database
from config import PROJECT_NAME, UPLOAD_DIR
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(
    title=PROJECT_NAME,
    description="羽毛球装备品类库与 RAG AI 选品系统后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    return {"status": "ok", "project": PROJECT_NAME}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
