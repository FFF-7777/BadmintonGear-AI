"""
购物车路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.cart import Cart
from models.product import Product
from schemas.schemas import CartAddRequest, CartUpdateRequest, CartOut
from utils.deps import get_current_user
from utils.resp import success, error

router = APIRouter(prefix="/api/cart", tags=["购物车"])


def _cart_to_dict(cart: Cart, product: Product) -> dict:
    """购物车项转字典"""
    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "product_id": cart.product_id,
        "quantity": cart.quantity,
        "checked": cart.checked,
        "product_name": product.name,
        "product_image": product.image,
        "product_price": float(product.price),
        "product_stock": product.stock,
        "create_time": cart.create_time,
    }


@router.get("/list")
def cart_list(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """获取当前用户购物车列表"""
    carts = db.query(Cart).filter(Cart.user_id == user.id).order_by(Cart.id.desc()).all()
    result = []
    for cart in carts:
        product = db.query(Product).filter(Product.id == cart.product_id).first()
        if product:
            result.append(_cart_to_dict(cart, product))
    return success(result)


@router.post("/add")
def add_to_cart(
    req: CartAddRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """添加装备到购物车"""
    product = db.query(Product).filter(Product.id == req.product_id, Product.status == 1).first()
    if not product:
        return error("装备不存在或已下架", 404)

    cart = db.query(Cart).filter(Cart.user_id == user.id, Cart.product_id == req.product_id).first()
    if cart:
        cart.quantity += req.quantity
    else:
        cart = Cart(user_id=user.id, product_id=req.product_id, quantity=req.quantity)
        db.add(cart)
    db.commit()
    return success(None, "添加成功")


@router.put("/{cart_id}")
def update_cart(
    cart_id: int,
    req: CartUpdateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """更新购物车项"""
    cart = db.query(Cart).filter(Cart.id == cart_id, Cart.user_id == user.id).first()
    if not cart:
        return error("购物车项不存在", 404)
    if req.quantity is not None:
        cart.quantity = req.quantity
    if req.checked is not None:
        cart.checked = req.checked
    db.commit()
    return success(None, "更新成功")


@router.delete("/{cart_id}")
def delete_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """删除购物车项"""
    cart = db.query(Cart).filter(Cart.id == cart_id, Cart.user_id == user.id).first()
    if not cart:
        return error("购物车项不存在", 404)
    db.delete(cart)
    db.commit()
    return success(None, "删除成功")


@router.delete("/clear/all")
def clear_cart(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """清空购物车"""
    db.query(Cart).filter(Cart.user_id == user.id).delete()
    db.commit()
    return success(None, "清空成功")
