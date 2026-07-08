"""Pydantic 请求/响应模型。"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="用户名")
    password: str = Field(..., min_length=6, max_length=32, description="密码")
    phone: Optional[str] = Field(None, max_length=11, description="手机号")
    nickname: Optional[str] = Field(None, max_length=20, description="昵称")


class PageQuery(BaseModel):
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="搜索关键词")


class CategoryCreate(BaseModel):
    name: str
    sort: int = 0
    status: int = 1


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[int] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    sort: int
    status: int
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    category_id: int
    name: str
    brand: Optional[str] = None
    series: Optional[str] = None
    model_aliases: Optional[list] = Field(None, description="型号别名 JSON 数组")
    description: Optional[str] = None
    specs: Optional[dict] = Field(None, description="结构化规格 JSON")
    price: Decimal = Field(..., description="参考价，仅用于预算对比")
    image: Optional[str] = None
    images: Optional[str] = None
    source_url: Optional[str] = None
    source_note: Optional[str] = None
    tags: Optional[list] = Field(None, description="系统标签 JSON 数组")
    manual_tags: Optional[list] = Field(None, description="人工标签 JSON 数组")
    status: int = 1


class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    brand: Optional[str] = None
    series: Optional[str] = None
    model_aliases: Optional[list] = Field(None, description="型号别名 JSON 数组")
    description: Optional[str] = None
    specs: Optional[dict] = Field(None, description="结构化规格 JSON")
    price: Optional[Decimal] = Field(None, description="参考价，仅用于预算对比")
    image: Optional[str] = None
    images: Optional[str] = None
    source_url: Optional[str] = None
    source_note: Optional[str] = None
    tags: Optional[list] = Field(None, description="系统标签 JSON 数组")
    manual_tags: Optional[list] = Field(None, description="人工标签 JSON 数组")
    status: Optional[int] = None


class ProductOut(BaseModel):
    id: int
    category_id: int
    name: str
    brand: Optional[str] = None
    series: Optional[str] = None
    model_aliases: Optional[list] = None
    description: Optional[str] = None
    specs: Optional[dict] = None
    price: Decimal
    image: Optional[str] = None
    images: Optional[str] = None
    source_url: Optional[str] = None
    source_note: Optional[str] = None
    tags: Optional[list] = None
    manual_tags: Optional[list] = None
    status: int
    category_name: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class BannerCreate(BaseModel):
    title: Optional[str] = None
    image: str
    link_type: int = 0
    link_id: int = 0
    sort: int = 0
    status: int = 1


class BannerUpdate(BaseModel):
    title: Optional[str] = None
    image: Optional[str] = None
    link_type: Optional[int] = None
    link_id: Optional[int] = None
    sort: Optional[int] = None
    status: Optional[int] = None


class BannerOut(BaseModel):
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


class UserOut(BaseModel):
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
    status: int


class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = Field(None, max_length=20, description="昵称")
    avatar: Optional[str] = Field(None, description="头像 URL")
    phone: Optional[str] = Field(None, max_length=11, description="手机号")


class UserPasswordUpdate(BaseModel):
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=32, description="新密码")


class AdminOut(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    status: int

    class Config:
        from_attributes = True


class AdminProfileUpdate(BaseModel):
    nickname: Optional[str] = Field(None, description="昵称")
    avatar: Optional[str] = Field(None, description="头像 URL")


class AdminPasswordUpdate(BaseModel):
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class KnowledgeFileOut(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_path: str
    brand: Optional[str] = None
    series: Optional[str] = None
    model_aliases: Optional[str] = None
    doc_type: Optional[str] = None
    file_size: int
    chunk_count: int
    status: int
    error_msg: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="用户消息")
    session_id: Optional[str] = Field(None, max_length=64, description="会话 ID")


class ChatMessageOut(BaseModel):
    id: int
    user_id: int
    session_id: str
    role: str
    content: str
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    messages: List[ChatMessageOut] = []
    recommended_products: List[dict] = []
