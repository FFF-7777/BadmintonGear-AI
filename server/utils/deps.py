"""
FastAPI依赖注入模块
提供当前用户和管理员身份验证
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from models.admin import Admin
from models.user import User
from utils.security import decode_access_token

# HTTP Bearer认证方案
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    获取当前登录用户
    :param credentials: 认证凭证
    :param db: 数据库会话
    :return: 当前用户对象
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or payload.get("type") != "user":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id), User.status == 1).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")
    return user


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Admin:
    """
    获取当前登录管理员
    :param credentials: 认证凭证
    :param db: 数据库会话
    :return: 当前管理员对象
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or payload.get("type") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")
    admin_id = payload.get("sub")
    admin = db.query(Admin).filter(Admin.id == int(admin_id), Admin.status == 1).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="管理员不存在或已禁用")
    return admin
