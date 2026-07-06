"""
数据统计Dashboard路由
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.category import Category
from models.order import Order, OrderItem
from models.product import Product
from models.user import User
from utils.deps import get_current_admin
from utils.resp import success

router = APIRouter(prefix="/api/dashboard", tags=["数据统计"])


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    获取Dashboard统计数据
    包含: 用户总数、订单总数、总销售额、近7日趋势、分类占比、热销装备
    """
    user_count = db.query(User).count()
    order_count = db.query(Order).filter(Order.status.in_([1, 2, 3])).count()
    total_sales = db.query(func.coalesce(func.sum(Order.pay_amount), 0)).filter(
        Order.status.in_([1, 2, 3])
    ).scalar()

    # 近7日订单趋势（按日期分组，避免时间边界导致统计遗漏）
    today = datetime.now().date()
    trend_dates = []
    trend_orders = []
    trend_sales = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = db.query(Order).filter(func.date(Order.create_time) == day).count()
        sales = db.query(func.coalesce(func.sum(Order.pay_amount), 0)).filter(
            func.date(Order.create_time) == day,
            Order.status.in_([1, 2, 3]),
        ).scalar()
        trend_dates.append(day.strftime("%Y-%m-%d"))
        trend_orders.append(count)
        trend_sales.append(float(sales))

    # 装备分类占比
    categories = db.query(Category).filter(Category.status == 1).all()
    category_stats = []
    for cat in categories:
        count = db.query(Product).filter(Product.category_id == cat.id).count()
        category_stats.append({"name": cat.name, "value": count})

    # 热销装备Top5
    top_products = (
        db.query(Product.id, Product.name, Product.sales, Product.price)
        .filter(Product.status == 1)
        .order_by(Product.sales.desc())
        .limit(5)
        .all()
    )
    hot_products = [
        {"id": p.id, "name": p.name, "sales": p.sales, "price": float(p.price)}
        for p in top_products
    ]

    # 订单状态分布
    status_map = {0: "待支付", 1: "已支付", 2: "已发货", 3: "已完成", 4: "已取消"}
    status_stats = []
    for s, label in status_map.items():
        count = db.query(Order).filter(Order.status == s).count()
        status_stats.append({"name": label, "value": count})

    return success({
        "user_count": user_count,
        "order_count": order_count,
        "total_sales": float(total_sales),
        "trend_dates": trend_dates,
        "trend_orders": trend_orders,
        "trend_sales": trend_sales,
        "category_stats": category_stats,
        "hot_products": hot_products,
        "status_stats": status_stats,
    })
