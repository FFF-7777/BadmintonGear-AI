"""
FastAPI应用入口
基于LangChain的羽毛球装备智能导购小程序
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import PROJECT_NAME, UPLOAD_DIR
from routers import auth, category, product, banner, cart, order, admin_user, dashboard, knowledge, chat, upload, admin_profile, user_profile, address

# 创建FastAPI应用
app = FastAPI(
    title=PROJECT_NAME,
    description="基于LangChain RAG的羽毛球装备智能导购小程序后端API",
    version="1.0.0",
)

# 配置CORS跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录 D:/uploads14
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# 注册路由
app.include_router(auth.router)
app.include_router(category.router)
app.include_router(product.router)
app.include_router(banner.router)
app.include_router(cart.router)
app.include_router(order.router)
app.include_router(admin_user.router)
app.include_router(dashboard.router)
app.include_router(knowledge.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(admin_profile.router)
app.include_router(user_profile.router)
app.include_router(address.router)


@app.get("/")
async def root():
    """根路径健康检查"""
    return {"message": PROJECT_NAME, "status": "running"}


@app.get("/api/health")
async def health():
    """健康检查接口"""
    return {"status": "ok", "project": PROJECT_NAME}
