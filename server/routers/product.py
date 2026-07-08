"""
装备路由
"""
from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models.category import Category
from models.product import Product
from schemas.schemas import ProductCreate, ProductUpdate, ProductOut
from services.product_import import XLSX_MIME, build_template_xlsx, import_products, parse_import_rows
from utils.deps import get_current_admin
from utils.resp import success, error, page_result

router = APIRouter(prefix="/api/product", tags=["装备"])


def _product_to_dict(product: Product, db: Session) -> dict:
    """将装备对象转为字典(含分类名)"""
    data = ProductOut.model_validate(product).model_dump()
    cat = db.query(Category).filter(Category.id == product.category_id).first()
    data["category_name"] = cat.name if cat else ""
    return data


def _batch_attach_category_names(products: list, db: Session) -> list:
    """批量预取分类名，避免列表接口 N+1 查询。"""
    if not products:
        return products
    category_ids = {p.category_id for p in products}
    categories = (
        db.query(Category)
        .filter(Category.id.in_(category_ids))
        .all()
    )
    cat_map = {c.id: c.name for c in categories}
    for p in products:
        p._category_name_cache = cat_map.get(p.category_id, "")
    return products


def _product_to_dict_batch(product: Product, db: Session) -> dict:
    """使用预取的分类名缓存，避免逐条查询。"""
    data = ProductOut.model_validate(product).model_dump()
    data["category_name"] = getattr(product, "_category_name_cache", None) or ""
    if not data["category_name"]:
        cat = db.query(Category).filter(Category.id == product.category_id).first()
        data["category_name"] = cat.name if cat else ""
    return data


@router.get("/list")
def product_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: int = Query(None),
    keyword: str = Query(None),
    status: int = Query(1),
    db: Session = Depends(get_db),
):
    """获取装备列表(前台)"""
    query = db.query(Product).filter(Product.status == status)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if keyword:
        query = query.filter(Product.name.like(f"%{keyword}%"))
    total = query.count()
    items = query.order_by(Product.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    _batch_attach_category_names(items, db)
    return success(page_result([_product_to_dict_batch(i, db) for i in items], total, page, page_size))


@router.get("/detail/{product_id}")
def product_detail(product_id: int, db: Session = Depends(get_db)):
    """获取装备详情"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return error("装备不存在", 404)
    return success(_product_to_dict(product, db))


@router.get("/admin/list")
def admin_product_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: int = Query(None),
    keyword: str = Query(None),
    status: int = Query(None),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """管理员分页查询装备"""
    query = db.query(Product)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if keyword:
        query = query.filter(Product.name.like(f"%{keyword}%"))
    if status is not None:
        query = query.filter(Product.status == status)
    total = query.count()
    items = query.order_by(Product.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    _batch_attach_category_names(items, db)
    return success(page_result([_product_to_dict_batch(i, db) for i in items], total, page, page_size))


@router.post("/admin/create")
def create_product(
    req: ProductCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """创建装备"""
    product = Product(**req.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return success(_product_to_dict(product, db), "创建成功")


@router.put("/admin/{product_id}")
def update_product(
    product_id: int,
    req: ProductUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """更新装备"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return error("装备不存在", 404)
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(product, k, v)
    db.commit()
    return success(None, "更新成功")


@router.delete("/admin/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """删除装备"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return error("装备不存在", 404)
    db.delete(product)
    db.commit()
    return success(None, "删除成功")


@router.get("/admin/import-template")
def download_import_template(
    category_id: int = Query(..., description="品类ID"),
    admin=Depends(get_current_admin),
):
    if category_id not in {1, 2, 3, 4}:
        return error("仅支持四个固定品类模板", 400)
    content = build_template_xlsx(category_id)
    filename = f"product-import-template-{category_id}.xlsx"
    return Response(
        content=content,
        media_type=XLSX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/admin/import")
def import_product_excel(
    file: UploadFile = File(...),
    category_id: int = Query(None, description="可选，品类ID；为空时按模板字段自动识别"),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    filename = (file.filename or "").strip()
    if not filename:
        return error("文件名不能为空")
    try:
        raw = file.file.read()
        rows = parse_import_rows(filename, raw)
        result = import_products(db, rows, category_id=category_id)
        return success(result, f"成功导入 {result['success_count']} 条装备数据")
    except Exception as exc:
        db.rollback()
        return error(f"导入失败: {str(exc)}", 400)
