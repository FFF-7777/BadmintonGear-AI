"""
装备分类路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.category import Category
from schemas.schemas import CategoryCreate, CategoryUpdate, CategoryOut
from utils.deps import get_current_admin
from utils.resp import success, error, page_result

router = APIRouter(prefix="/api/category", tags=["装备分类"])


@router.get("/list")
def category_list(
    status: int = Query(None, description="状态筛选"),
    db: Session = Depends(get_db),
):
    """
    获取分类列表(前台/后台通用)
    """
    query = db.query(Category)
    if status is not None:
        query = query.filter(Category.status == status)
    items = query.order_by(Category.sort.asc(), Category.id.asc()).all()
    return success([CategoryOut.model_validate(i).model_dump() for i in items])


@router.get("/admin/list")
def admin_category_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(None),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    管理员分页查询分类列表
    """
    query = db.query(Category)
    if keyword:
        query = query.filter(Category.name.like(f"%{keyword}%"))
    total = query.count()
    items = query.order_by(Category.sort.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return success(page_result(
        [CategoryOut.model_validate(i).model_dump() for i in items],
        total, page, page_size,
    ))


@router.post("/admin/create")
def create_category(
    req: CategoryCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """创建装备分类"""
    cat = Category(**req.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return success(CategoryOut.model_validate(cat).model_dump(), "创建成功")


@router.put("/admin/{cat_id}")
def update_category(
    cat_id: int,
    req: CategoryUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """更新装备分类"""
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        return error("分类不存在", 404)
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    return success(None, "更新成功")


@router.delete("/admin/{cat_id}")
def delete_category(
    cat_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """删除装备分类"""
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        return error("分类不存在", 404)
    db.delete(cat)
    db.commit()
    return success(None, "删除成功")
