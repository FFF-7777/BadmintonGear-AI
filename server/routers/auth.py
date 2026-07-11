"""
认证路由
提供用户/管理员登录和注册接口，带 rate limiting 防暴力破解。
"""
import re

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from config import RATE_LIMIT_LOGIN, RATE_LIMIT_REGISTER
from database import get_db
from models.admin import Admin
from models.user import User
from schemas.schemas import LoginRequest, RegisterRequest
from utils.rate_limit import limiter
from utils.resp import success, error
from utils.security import verify_password, hash_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/admin/login")
@limiter.limit(RATE_LIMIT_LOGIN)
def admin_login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    """
    管理员登录
    :param req: 登录请求(用户名+密码)
    :param db: 数据库会话
    :return: JWT令牌
    """
    admin = db.query(Admin).filter(Admin.username == req.username).first()
    if not admin or not verify_password(req.password, admin.password):
        return error("用户名或密码错误", 401)
    if admin.status != 1:
        return error("账号已被禁用", 403)

    token = create_access_token({"sub": str(admin.id), "type": "admin"})
    return success({
        "token": token,
        "user_type": "admin",
        "user_id": admin.id,
        "username": admin.username,
        "nickname": admin.nickname,
        "avatar": admin.avatar,
    }, "登录成功")


@router.post("/user/login")
@limiter.limit(RATE_LIMIT_LOGIN)
def user_login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录(小程序/前台)
    :param req: 登录请求
    :param db: 数据库会话
    :return: JWT令牌
    """
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password):
        return error("用户名或密码错误", 401)
    if user.status != 1:
        return error("账号已被禁用", 403)

    token = create_access_token({"sub": str(user.id), "type": "user"})
    return success({
        "token": token,
        "user_type": "user",
        "user_id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "phone": user.phone,
    }, "登录成功")


@router.post("/user/register")
@limiter.limit(RATE_LIMIT_REGISTER)
def user_register(request: Request, req: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册
    :param req: 注册请求
    :param db: 数据库会话
    :return: 注册结果
    """
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", req.username):
        return error("用户名需3-20位字母、数字或下划线")

    if req.phone and not re.match(r"^1[3-9]\d{9}$", req.phone):
        return error("手机号格式不正确")

    exists = db.query(User).filter(User.username == req.username).first()
    if exists:
        return error("用户名已存在")

    if req.phone:
        phone_exists = db.query(User).filter(User.phone == req.phone).first()
        if phone_exists:
            return error("手机号已被注册")

    user = User(
        username=req.username,
        password=hash_password(req.password),
        phone=req.phone,
        nickname=req.nickname or req.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success({"user_id": user.id}, "注册成功")
