"""
用户个人资料路由
支持资料修改、密码修改
"""
import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.schemas import UserOut, UserProfileUpdate, UserPasswordUpdate
from utils.deps import get_current_user
from utils.resp import success, error
from utils.security import verify_password, hash_password

router = APIRouter(prefix="/api/user/profile", tags=["用户资料"])


@router.get("/me")
def get_profile(user: User = Depends(get_current_user)):
    """获取当前用户资料"""
    return success(UserOut.model_validate(user).model_dump())


@router.put("")
def update_profile(
    req: UserProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新用户资料(昵称、头像、手机号)"""
    if req.nickname is not None:
        nickname = req.nickname.strip()
        if not nickname:
            return error("昵称不能为空")
        if len(nickname) > 20:
            return error("昵称不能超过20个字符")
        user.nickname = nickname

    if req.avatar is not None:
        user.avatar = req.avatar.strip() or None

    if req.phone is not None:
        phone = req.phone.strip()
        if phone:
            if not re.match(r"^1[3-9]\d{9}$", phone):
                return error("手机号格式不正确")
            phone_exists = db.query(User).filter(User.phone == phone, User.id != user.id).first()
            if phone_exists:
                return error("手机号已被其他账号使用")
        user.phone = phone or None

    db.commit()
    db.refresh(user)
    return success(UserOut.model_validate(user).model_dump(), "资料更新成功")


@router.put("/password")
def change_password(
    req: UserPasswordUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """修改用户密码"""
    if not verify_password(req.old_password, user.password):
        return error("原密码错误", 400)
    if req.old_password == req.new_password:
        return error("新密码不能与原密码相同", 400)

    user.password = hash_password(req.new_password)
    db.commit()
    return success(None, "密码修改成功")
