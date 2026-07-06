"""
订单路由
"""
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.order import Order, OrderItem
from models.product import Product
from models.user import User
from schemas.schemas import OrderCreateRequest, OrderOut, OrderItemOut, OrderStatusUpdate
from utils.deps import get_current_user, get_current_admin
from utils.resp import success, error, page_result

router = APIRouter(prefix="/api/order", tags=["订单"])


def _generate_order_no() -> str:
    """生成订单编号"""
    return datetime.now().strftime("%Y%m%d%H%M%S") + str(datetime.now().microsecond)[:4]


def _order_to_dict(order: Order, db: Session, include_items: bool = True) -> dict:
    """订单转字典"""
    data = OrderOut.model_validate(order).model_dump()
    user = db.query(User).filter(User.id == order.user_id).first()
    data["username"] = user.username if user else ""
    if include_items:
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        data["items"] = [OrderItemOut.model_validate(i).model_dump() for i in items]
    return data


@router.post("/create")
def create_order(
    req: OrderCreateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    创建订单
    """
    if not req.items:
        return error("订单装备不能为空")

    total = Decimal("0")
    order_items = []
    for item in req.items:
        product = db.query(Product).filter(Product.id == item.product_id, Product.status == 1).first()
        if not product:
            return error(f"装备ID {item.product_id} 不存在或已下架")
        if product.stock < item.quantity:
            return error(f"装备 {product.name} 库存不足")
        subtotal = product.price * item.quantity
        total += subtotal
        order_items.append({
            "product": product,
            "quantity": item.quantity,
            "subtotal": subtotal,
        })

    order = Order(
        order_no=_generate_order_no(),
        user_id=user.id,
        total_amount=total,
        pay_amount=total,
        status=0,
        receiver_name=req.receiver_name,
        receiver_phone=req.receiver_phone,
        receiver_address=req.receiver_address,
        remark=req.remark,
    )
    db.add(order)
    db.flush()

    for oi in order_items:
        p = oi["product"]
        db.add(OrderItem(
            order_id=order.id,
            product_id=p.id,
            product_name=p.name,
            product_image=p.image,
            price=p.price,
            quantity=oi["quantity"],
            total_price=oi["subtotal"],
        ))
        p.stock -= oi["quantity"]

    db.commit()
    db.refresh(order)
    return success(_order_to_dict(order, db), "下单成功")


@router.post("/pay/{order_id}")
def pay_order(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    模拟支付订单
    """
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        return error("订单不存在", 404)
    if order.status != 0:
        return error("订单状态不允许支付")

    order.status = 1
    order.pay_time = datetime.now()
    # 更新销量
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.sales += item.quantity
    db.commit()
    return success(None, "支付成功")


@router.get("/my/list")
def my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: int = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """获取当前用户订单列表"""
    query = db.query(Order).filter(Order.user_id == user.id)
    if status is not None:
        query = query.filter(Order.status == status)
    total = query.count()
    orders = query.order_by(Order.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return success(page_result([_order_to_dict(o, db) for o in orders], total, page, page_size))


@router.get("/detail/{order_id}")
def order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """获取订单详情"""
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        return error("订单不存在", 404)
    return success(_order_to_dict(order, db))


@router.get("/admin/list")
def admin_order_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: int = Query(None),
    keyword: str = Query(None),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """管理员分页查询订单"""
    query = db.query(Order)
    if status is not None:
        query = query.filter(Order.status == status)
    if keyword:
        query = query.filter(Order.order_no.like(f"%{keyword}%"))
    total = query.count()
    orders = query.order_by(Order.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return success(page_result([_order_to_dict(o, db) for o in orders], total, page, page_size))


@router.put("/admin/{order_id}/status")
def update_order_status(
    order_id: int,
    req: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """管理员更新订单状态"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return error("订单不存在", 404)
    order.status = req.status
    db.commit()
    return success(None, "状态更新成功")
