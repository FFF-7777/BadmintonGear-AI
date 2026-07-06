"""
Pydantic请求/响应模型
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


# ==================== 通用 ====================

class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class RegisterRequest(BaseModel):
    """用户注册请求模型"""
    username: str = Field(..., min_length=3, max_length=20, description="用户名")
    password: str = Field(..., min_length=6, max_length=32, description="密码")
    phone: Optional[str] = Field(None, max_length=11, description="手机号")
    nickname: Optional[str] = Field(None, max_length=20, description="昵称")


class TokenResponse(BaseModel):
    """令牌响应模型"""
    token: str
    user_type: str
    user_id: int
    username: str
    nickname: Optional[str] = None


class PageQuery(BaseModel):
    """分页查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页大小")
    keyword: Optional[str] = Field(None, description="搜索关键词")


# ==================== 分类 ====================

class CategoryCreate(BaseModel):
    """创建分类请求"""
    name: str
    sort: int = 0
    status: int = 1


class CategoryUpdate(BaseModel):
    """更新分类请求"""
    name: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[int] = None


class CategoryOut(BaseModel):
    """分类响应"""
    id: int
    name: str
    sort: int
    status: int
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 装备 ====================

class ProductCreate(BaseModel):
    """创建装备请求"""
    category_id: int
    name: str
    description: Optional[str] = None
    specs: Optional[dict] = Field(None, description="结构化规格(JSON)")
    price: Decimal
    stock: int = 0
    image: Optional[str] = None
    images: Optional[str] = None
    status: int = 1


class ProductUpdate(BaseModel):
    """更新装备请求"""
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    specs: Optional[dict] = Field(None, description="结构化规格(JSON)")
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    image: Optional[str] = None
    images: Optional[str] = None
    status: Optional[int] = None


class ProductOut(BaseModel):
    """装备响应"""
    id: int
    category_id: int
    name: str
    description: Optional[str] = None
    specs: Optional[dict] = None
    price: Decimal
    stock: int
    image: Optional[str] = None
    images: Optional[str] = None
    sales: int
    status: int
    category_name: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 轮播图 ====================

class BannerCreate(BaseModel):
    """创建轮播图请求"""
    title: Optional[str] = None
    image: str
    link_type: int = 0
    link_id: int = 0
    sort: int = 0
    status: int = 1


class BannerUpdate(BaseModel):
    """更新轮播图请求"""
    title: Optional[str] = None
    image: Optional[str] = None
    link_type: Optional[int] = None
    link_id: Optional[int] = None
    sort: Optional[int] = None
    status: Optional[int] = None


class BannerOut(BaseModel):
    """轮播图响应"""
    id: int
    title: Optional[str] = None
    image: str
    link_type: int
    link_id: int
    sort: int
    status: int
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 购物车 ====================

class CartAddRequest(BaseModel):
    """添加购物车请求"""
    product_id: int
    quantity: int = 1


class CartUpdateRequest(BaseModel):
    """更新购物车请求"""
    quantity: Optional[int] = None
    checked: Optional[int] = None


class CartOut(BaseModel):
    """购物车响应"""
    id: int
    user_id: int
    product_id: int
    quantity: int
    checked: int
    product_name: Optional[str] = None
    product_image: Optional[str] = None
    product_price: Optional[Decimal] = None
    product_stock: Optional[int] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 收货地址 ====================

class AddressCreate(BaseModel):
    """创建收货地址"""
    name: str = Field(..., max_length=50, description="收货人")
    phone: str = Field(..., max_length=20, description="联系电话")
    address: str = Field(..., max_length=255, description="详细地址")
    is_default: int = Field(0, description="是否默认:1是0否")


class AddressUpdate(BaseModel):
    """更新收货地址"""
    name: Optional[str] = Field(None, max_length=50, description="收货人")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    address: Optional[str] = Field(None, max_length=255, description="详细地址")
    is_default: Optional[int] = Field(None, description="是否默认:1是0否")


class AddressOut(BaseModel):
    """收货地址响应"""
    id: int
    user_id: int
    name: str
    phone: str
    address: str
    is_default: int
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 订单 ====================

class OrderItemCreate(BaseModel):
    """订单明细创建"""
    product_id: int
    quantity: int


class OrderCreateRequest(BaseModel):
    """创建订单请求"""
    items: List[OrderItemCreate]
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    remark: Optional[str] = None


class OrderItemOut(BaseModel):
    """订单明细响应"""
    id: int
    product_id: int
    product_name: str
    product_image: Optional[str] = None
    price: Decimal
    quantity: int
    total_price: Decimal

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    """订单响应"""
    id: int
    order_no: str
    user_id: int
    total_amount: Decimal
    pay_amount: Decimal
    status: int
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_address: Optional[str] = None
    remark: Optional[str] = None
    pay_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    items: Optional[List[OrderItemOut]] = None
    username: Optional[str] = None

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    """订单状态更新"""
    status: int


# ==================== 用户/管理员 ====================

class UserOut(BaseModel):
    """用户响应"""
    id: int
    username: str
    phone: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    status: int
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserStatusUpdate(BaseModel):
    """用户状态更新"""
    status: int


class UserProfileUpdate(BaseModel):
    """用户资料更新"""
    nickname: Optional[str] = Field(None, max_length=20, description="昵称")
    avatar: Optional[str] = Field(None, description="头像URL")
    phone: Optional[str] = Field(None, max_length=11, description="手机号")


class UserPasswordUpdate(BaseModel):
    """用户密码修改"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=32, description="新密码")


class AdminOut(BaseModel):
    """管理员响应"""
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    status: int

    class Config:
        from_attributes = True


class AdminProfileUpdate(BaseModel):
    """管理员资料更新"""
    nickname: Optional[str] = Field(None, description="昵称")
    avatar: Optional[str] = Field(None, description="头像URL")


class AdminPasswordUpdate(BaseModel):
    """管理员密码修改"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, description="新密码")


# ==================== 知识库 ====================

class KnowledgeFileOut(BaseModel):
    """知识库文件响应"""
    id: int
    file_name: str
    file_type: str
    file_path: str
    file_size: int
    chunk_count: int
    status: int
    error_msg: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== AI聊天 ====================

class ChatRequest(BaseModel):
    """AI聊天请求"""
    message: str = Field(..., min_length=1, max_length=1000, description="用户消息")
    session_id: Optional[str] = Field(None, max_length=64, description="会话ID")


class ChatMessageOut(BaseModel):
    """聊天消息响应"""
    id: int
    user_id: int
    session_id: str
    role: str
    content: str
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """AI聊天响应"""
    session_id: str
    answer: str
    messages: List[ChatMessageOut] = []
    recommended_products: List[dict] = []
