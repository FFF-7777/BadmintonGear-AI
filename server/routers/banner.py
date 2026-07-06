"""
轮播图路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.banner import Banner
from schemas.schemas import BannerCreate, BannerUpdate, BannerOut
from utils.deps import get_current_admin
from utils.resp import success, error, page_result

router = APIRouter(prefix="/api/banner", tags=["轮播图"])


@router.get("/list")
def banner_list(db: Session = Depends(get_db)):
    """获取启用的轮播图列表(前台)"""
    items = db.query(Banner).filter(Banner.status == 1).order_by(Banner.sort.asc()).all()
    return success([BannerOut.model_validate(i).model_dump() for i in items])


@router.get("/admin/list")
def admin_banner_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """管理员分页查询轮播图"""
    query = db.query(Banner)
    total = query.count()
    items = query.order_by(Banner.sort.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return success(page_result(
        [BannerOut.model_validate(i).model_dump() for i in items],
        total, page, page_size,
    ))


@router.post("/admin/create")
def create_banner(
    req: BannerCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """创建轮播图"""
    banner = Banner(**req.model_dump())
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return success(BannerOut.model_validate(banner).model_dump(), "创建成功")


@router.put("/admin/{banner_id}")
def update_banner(
    banner_id: int,
    req: BannerUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """更新轮播图"""
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        return error("轮播图不存在", 404)
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(banner, k, v)
    db.commit()
    return success(None, "更新成功")


@router.delete("/admin/{banner_id}")
def delete_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """删除轮播图"""
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        return error("轮播图不存在", 404)
    db.delete(banner)
    db.commit()
    return success(None, "删除成功")
