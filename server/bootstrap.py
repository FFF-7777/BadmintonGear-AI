"""Local database bootstrap for development."""
from decimal import Decimal

from sqlalchemy import inspect, text

from database import Base, SessionLocal, engine
from models.admin import Admin
from models.banner import Banner
from models.category import Category
from models.chat import ChatMessage
from models.knowledge import KnowledgeFile
from models.product import Product
from models.user import User
from services.rag_pipeline import infer_brand, infer_series
from utils.security import md5_hash


PRODUCT_EXTRA_COLUMNS = {
    "brand": {"default": "VARCHAR(50)"},
    "series": {"default": "VARCHAR(100)"},
    "model_aliases": {"sqlite": "TEXT", "mysql": "JSON", "default": "TEXT"},
    "source_url": {"default": "VARCHAR(500)"},
    "source_note": {"default": "VARCHAR(255)"},
    "tags": {"sqlite": "TEXT", "mysql": "JSON", "default": "TEXT"},
    "manual_tags": {"sqlite": "TEXT", "mysql": "JSON", "default": "TEXT"},
}

KNOWLEDGE_EXTRA_COLUMNS = {
    "brand": {"default": "VARCHAR(50)"},
    "series": {"default": "VARCHAR(100)"},
    "model_aliases": {"default": "VARCHAR(500)"},
    "doc_type": {"default": "VARCHAR(30)"},
}


def _ensure_product_schema() -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("t_product")} if inspector.has_table("t_product") else set()
    if not columns:
        return

    with engine.begin() as conn:
        dialect = engine.dialect.name
        for column_name, column_types in PRODUCT_EXTRA_COLUMNS.items():
            if column_name in columns:
                continue
            column_type = column_types.get(dialect, column_types["default"])
            conn.execute(text(f"ALTER TABLE t_product ADD COLUMN {column_name} {column_type}"))


def _ensure_knowledge_schema() -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("t_knowledge_file")} if inspector.has_table("t_knowledge_file") else set()
    if not columns:
        return

    with engine.begin() as conn:
        dialect = engine.dialect.name
        for column_name, column_types in KNOWLEDGE_EXTRA_COLUMNS.items():
            if column_name in columns:
                continue
            column_type = column_types.get(dialect, column_types["default"])
            conn.execute(text(f"ALTER TABLE t_knowledge_file ADD COLUMN {column_name} {column_type}"))


def init_database() -> None:
    """Create tables and seed minimal local data when the database is empty."""
    Base.metadata.create_all(bind=engine)
    _ensure_product_schema()
    _ensure_knowledge_schema()

    db = SessionLocal()
    try:
        if not db.query(Admin).filter(Admin.username == "admin").first():
            db.add(Admin(
                username="admin",
                password=md5_hash("admin"),
                nickname="羽智选管理员",
                status=1,
            ))

        if db.query(Category).count() == 0:
            db.add_all([
                Category(id=1, name="球拍", sort=10, status=1),
                Category(id=2, name="球线", sort=20, status=1),
                Category(id=3, name="羽毛球", sort=30, status=1),
                Category(id=4, name="球鞋", sort=40, status=1),
            ])

        if db.query(Product).count() == 0:
            db.add_all([
                Product(
                    category_id=1,
                    name="YONEX 天斧 77 Pro",
                    brand="YONEX",
                    series="天斧",
                    model_aliases=["AX77PRO", "ASTROX 77 PRO", "天斧77PRO"],
                    description="偏进攻但不极端，适合想增强后场下压的进阶玩家。",
                    specs={
                        "brand": "YONEX",
                        "weight_class": "4U",
                        "balance": "head-heavy",
                        "shaft_flex": "medium",
                        "suitable_level": ["intermediate", "advanced"],
                        "suitable_style": ["attack", "balanced"],
                        "level": "进阶 / 比赛",
                        "best_for": "单打、后场进攻、力量中等以上",
                    },
                    price=Decimal("1100.00"),
                    image="/assets/products/racket-astrox-77.svg",
                    tags=["进攻", "进阶"],
                    status=1,
                ),
                Product(
                    category_id=1,
                    name="李宁 战戟 6000",
                    brand="LI-NING",
                    series="战戟",
                    model_aliases=["HAL6000", "HALBERTEC 6000", "战戟6000"],
                    description="均衡型球拍，容错和控制较好，适合从入门迈向进阶。",
                    specs={
                        "brand": "LI-NING",
                        "weight_class": "4U",
                        "balance": "even-balanced",
                        "shaft_flex": "medium",
                        "suitable_level": ["beginner", "intermediate"],
                        "suitable_style": ["balanced", "control"],
                        "level": "入门进阶",
                        "best_for": "双打、攻守均衡",
                    },
                    price=Decimal("680.00"),
                    image="/assets/products/racket-halbertec-6000.svg",
                    tags=["均衡", "新手友好"],
                    status=1,
                ),
                Product(
                    category_id=1,
                    name="VICTOR 极速 JS-12",
                    brand="VICTOR",
                    series="极速",
                    model_aliases=["JS12", "JETSPEED 12", "极速12"],
                    description="速度型经典思路，平抽挡和防守转换更轻快。",
                    specs={
                        "brand": "VICTOR",
                        "weight_class": "4U",
                        "balance": "head-light",
                        "shaft_flex": "medium",
                        "suitable_level": ["intermediate", "advanced"],
                        "suitable_style": ["defense", "control"],
                        "level": "进阶",
                        "best_for": "双打、平抽挡、网前封网",
                    },
                    price=Decimal("850.00"),
                    image="/assets/products/racket-js12.svg",
                    tags=["速度", "双打"],
                    status=1,
                ),
                Product(
                    category_id=1,
                    name="川崎 入门均衡拍",
                    brand="KAWASAKI",
                    description="预算友好，适合新手建立动作和基础手感。",
                    specs={
                        "brand": "KAWASAKI",
                        "weight_class": "4U",
                        "balance": "even-balanced",
                        "shaft_flex": "flexible",
                        "suitable_level": ["beginner"],
                        "suitable_style": ["balanced"],
                        "level": "入门",
                        "best_for": "新手、校园、休闲训练",
                    },
                    price=Decimal("260.00"),
                    image="/assets/products/racket-kawasaki-entry.svg",
                    tags=["预算", "新手友好"],
                    status=1,
                ),
                Product(
                    category_id=2,
                    name="YONEX BG80",
                    brand="YONEX",
                    model_aliases=["BG80"],
                    description="0.68mm 经典进攻线，出球直接，控制和弹性平衡。",
                    specs={"brand": "YONEX", "gauge": "0.68", "feel": "hard", "durability": "high", "repulsion": "high"},
                    price=Decimal("58.00"),
                    image="/assets/products/string-bg80.svg",
                    tags=["进攻", "耐打"],
                    status=1,
                ),
                Product(
                    category_id=2,
                    name="YONEX BG65",
                    brand="YONEX",
                    model_aliases=["BG65"],
                    description="耐打代表，适合训练量大或经常断线的用户。",
                    specs={"brand": "YONEX", "gauge": "0.70", "feel": "stable", "durability": "high"},
                    price=Decimal("45.00"),
                    image="/assets/products/string-bg65.svg",
                    tags=["耐打", "训练"],
                    status=1,
                ),
                Product(
                    category_id=2,
                    name="李宁 1号线",
                    brand="LI-NING",
                    model_aliases=["NO1", "NO.1", "1号线"],
                    description="弹性和声音表现突出，适合追求清脆击球反馈。", 
                    specs={"brand": "LI-NING", "gauge": "0.65", "feel": "medium", "repulsion": "high", "durability": "medium"},
                    price=Decimal("55.00"),
                    image="/assets/products/string-no1.svg",
                    tags=["高弹", "手感"],
                    status=1,
                ),
                Product(
                    category_id=3,
                    name="YONEX AS-05",
                    brand="YONEX",
                    model_aliases=["AS05", "AS-05"],
                    description="训练和日常对抗常见选择，稳定性和价格较均衡。",
                    specs={"brand": "YONEX", "material": "duck_feather", "speed": "77", "usage_scene": "训练 / 日常"},
                    price=Decimal("100.00"),
                    image="/assets/products/shuttle-as05.svg",
                    tags=["训练", "稳定"],
                    status=1,
                ),
                Product(
                    category_id=3,
                    name="李宁 A+ 系列训练球",
                    brand="LI-NING",
                    series="A+",
                    description="适合训练消耗，兼顾耐打和稳定。",
                    specs={"brand": "LI-NING", "material": "duck_feather", "usage_scene": "训练", "durability": "high"},
                    price=Decimal("85.00"),
                    image="/assets/products/shuttle-lining-a6.svg",
                    tags=["训练", "耐打"],
                    status=1,
                ),
                Product(
                    category_id=4,
                    name="YONEX 65Z",
                    brand="YONEX",
                    series="65Z",
                    model_aliases=["65Z", "65Z3", "POWER CUSHION 65Z"],
                    description="经典比赛鞋，缓震、包裹和启动表现均衡。",
                    specs={"brand": "YONEX", "cushion_score": 9.2, "support_score": 8.8, "width_fit": "regular", "level": "进阶 / 比赛"},
                    price=Decimal("820.00"),
                    image="/assets/products/shoes-65z.svg",
                    tags=["高缓震", "比赛"],
                    status=1,
                ),
                Product(
                    category_id=4,
                    name="李宁 雷霆 / 鹘鹰系球鞋",
                    brand="LI-NING",
                    series="雷霆",
                    description="缓震和支撑表现突出，适合高强度移动。",
                    specs={"brand": "LI-NING", "cushion_score": 8.9, "support_score": 8.7, "width_fit": "wide-friendly", "level": "进阶"},
                    price=Decimal("650.00"),
                    image="/assets/products/shoes-lining-ayzr.svg",
                    tags=["高缓震", "宽脚友好"],
                    status=1,
                ),
                Product(
                    category_id=4,
                    name="VICTOR P9200 系列",
                    brand="VICTOR",
                    series="P9200",
                    model_aliases=["P9200"],
                    description="稳定和保护取向，适合双打多启动场景。",
                    specs={"brand": "VICTOR", "cushion_score": 8.4, "support_score": 8.9, "width_fit": "regular", "level": "进阶"},
                    price=Decimal("600.00"),
                    image="/assets/products/shoes-victor-p9200.svg",
                    tags=["稳定", "双打"],
                    status=1,
                ),
            ])

        for product in db.query(Product).all():
            specs = product.specs or {}
            if not product.brand:
                product.brand = specs.get("brand") or infer_brand(product.name) or ""
            if not product.series:
                product.series = infer_series(f"{product.name} {product.description or ''}") or ""

        db.commit()
    finally:
        db.close()
