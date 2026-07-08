"""管理端数据看板路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.category import Category
from models.chat import ChatMessage
from models.knowledge import KnowledgeFile
from models.product import Product
from models.user import User
from utils.deps import get_current_admin
from utils.resp import success

router = APIRouter(prefix="/api/dashboard", tags=["数据看板"])


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """返回装备库与 RAG 知识库维度的运营概览。"""
    user_count = db.query(User).count()
    product_count = db.query(Product).count()
    active_product_count = db.query(Product).filter(Product.status == 1).count()
    category_count = db.query(Category).filter(Category.status == 1).count()
    knowledge_count = db.query(KnowledgeFile).count()
    vectorized_knowledge_count = db.query(KnowledgeFile).filter(KnowledgeFile.status == 1).count()
    chat_message_count = db.query(ChatMessage).count()
    chat_session_count = db.query(func.count(func.distinct(ChatMessage.session_id))).scalar() or 0

    categories = db.query(Category).filter(Category.status == 1).order_by(Category.sort.asc()).all()
    category_stats = []
    for category in categories:
        count = db.query(Product).filter(Product.category_id == category.id).count()
        category_stats.append({"name": category.name, "value": count})

    knowledge_status_map = {0: "待处理", 1: "已向量化", 2: "失败"}
    knowledge_status_stats = []
    for status, label in knowledge_status_map.items():
        count = db.query(KnowledgeFile).filter(KnowledgeFile.status == status).count()
        knowledge_status_stats.append({"name": label, "value": count})

    latest_products = (
        db.query(Product.id, Product.name, Product.price)
        .filter(Product.status == 1)
        .order_by(Product.id.desc())
        .limit(5)
        .all()
    )

    return success({
        "user_count": user_count,
        "product_count": product_count,
        "active_product_count": active_product_count,
        "category_count": category_count,
        "knowledge_count": knowledge_count,
        "vectorized_knowledge_count": vectorized_knowledge_count,
        "chat_message_count": chat_message_count,
        "chat_session_count": chat_session_count,
        "category_stats": category_stats,
        "knowledge_status_stats": knowledge_status_stats,
        "latest_products": [
            {"id": row.id, "name": row.name, "price": float(row.price)}
            for row in latest_products
        ],
    })
