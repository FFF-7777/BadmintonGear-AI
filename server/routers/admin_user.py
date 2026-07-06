"""
用户管理路由(管理员)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.schemas import UserOut, UserStatusUpdate
from utils.deps import get_current_admin
from utils.resp import success, error, page_result

router = APIRouter(prefix="/api/admin/user", tags=["用户管理"])


@router.get("/list")
def user_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(None),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """管理员分页查询用户列表"""
    query = db.query(User)
    if keyword:
        query = query.filter(
            (User.username.like(f"%{keyword}%")) | (User.phone.like(f"%{keyword}%"))
        )
    total = query.count()
    items = query.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return success(page_result(
        [UserOut.model_validate(i).model_dump() for i in items],
        total, page, page_size,
    ))


@router.put("/{user_id}/status")
def update_user_status(
    user_id: int,
    req: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """更新用户状态"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error("用户不存在", 404)
    user.status = req.status
    db.commit()
    return success(None, "状态更新成功")
