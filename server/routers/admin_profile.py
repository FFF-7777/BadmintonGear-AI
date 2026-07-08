"""
管理员个人资料路由
支持资料修改、密码修改
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.admin import Admin
from schemas.schemas import AdminOut, AdminProfileUpdate, AdminPasswordUpdate
from utils.deps import get_current_admin
from utils.resp import success, error
from utils.security import verify_password, hash_password

router = APIRouter(prefix="/api/admin/profile", tags=["管理员资料"])


@router.get("/me")
def get_profile(admin: Admin = Depends(get_current_admin)):
    """获取当前管理员资料"""
    return success(AdminOut.model_validate(admin).model_dump())


@router.put("")
def update_profile(
    req: AdminProfileUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """更新管理员资料(昵称、头像)"""
    if req.nickname is not None:
        nickname = req.nickname.strip()
        if not nickname:
            return error("昵称不能为空")
        admin.nickname = nickname

    if req.avatar is not None:
        admin.avatar = req.avatar.strip() or None

    db.commit()
    db.refresh(admin)
    return success(AdminOut.model_validate(admin).model_dump(), "资料更新成功")


@router.put("/password")
def change_password(
    req: AdminPasswordUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """修改管理员密码"""
    if not verify_password(req.old_password, admin.password):
        return error("原密码错误", 400)
    if req.old_password == req.new_password:
        return error("新密码不能与原密码相同", 400)

    admin.password = hash_password(req.new_password)
    db.commit()
    return success(None, "密码修改成功")
