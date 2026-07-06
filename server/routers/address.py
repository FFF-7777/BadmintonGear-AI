"""
收货地址路由
"""
import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.address import Address
from schemas.schemas import AddressCreate, AddressUpdate, AddressOut
from utils.deps import get_current_user
from utils.resp import success, error

router = APIRouter(prefix="/api/address", tags=["收货地址"])


def _clear_default(db: Session, user_id: int, exclude_id: int = None):
    """取消用户其他默认地址"""
    query = db.query(Address).filter(Address.user_id == user_id, Address.is_default == 1)
    if exclude_id:
        query = query.filter(Address.id != exclude_id)
    query.update({Address.is_default: 0}, synchronize_session=False)


def _validate_phone(phone: str) -> bool:
    return bool(re.match(r"^1[3-9]\d{9}$", phone))


@router.get("/list")
def address_list(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """获取当前用户收货地址列表(默认地址排前)"""
    rows = (
        db.query(Address)
        .filter(Address.user_id == user.id)
        .order_by(Address.is_default.desc(), Address.id.desc())
        .all()
    )
    return success([AddressOut.model_validate(row).model_dump() for row in rows])


@router.get("/default")
def get_default_address(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """获取默认收货地址"""
    row = (
        db.query(Address)
        .filter(Address.user_id == user.id, Address.is_default == 1)
        .first()
    )
    if not row:
        row = (
            db.query(Address)
            .filter(Address.user_id == user.id)
            .order_by(Address.id.desc())
            .first()
        )
    if not row:
        return success(None)
    return success(AddressOut.model_validate(row).model_dump())


@router.get("/{address_id}")
def get_address(
    address_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """获取单个收货地址"""
    row = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not row:
        return error("地址不存在", 404)
    return success(AddressOut.model_validate(row).model_dump())


@router.post("")
def create_address(
    req: AddressCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """新增收货地址"""
    name = req.name.strip()
    phone = req.phone.strip()
    address = req.address.strip()
    if not name:
        return error("收货人不能为空")
    if not _validate_phone(phone):
        return error("手机号格式不正确")
    if not address:
        return error("详细地址不能为空")

    count = db.query(Address).filter(Address.user_id == user.id).count()
    is_default = 1 if req.is_default == 1 or count == 0 else 0
    if is_default:
        _clear_default(db, user.id)

    row = Address(
        user_id=user.id,
        name=name,
        phone=phone,
        address=address,
        is_default=is_default,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return success(AddressOut.model_validate(row).model_dump(), "添加成功")


@router.put("/{address_id}")
def update_address(
    address_id: int,
    req: AddressUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """更新收货地址"""
    row = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not row:
        return error("地址不存在", 404)

    if req.name is not None:
        name = req.name.strip()
        if not name:
            return error("收货人不能为空")
        row.name = name

    if req.phone is not None:
        phone = req.phone.strip()
        if not _validate_phone(phone):
            return error("手机号格式不正确")
        row.phone = phone

    if req.address is not None:
        address = req.address.strip()
        if not address:
            return error("详细地址不能为空")
        row.address = address

    if req.is_default is not None:
        if req.is_default == 1:
            _clear_default(db, user.id, exclude_id=row.id)
            row.is_default = 1
        else:
            if row.is_default == 1:
                other = (
                    db.query(Address)
                    .filter(Address.user_id == user.id, Address.id != row.id)
                    .order_by(Address.id.desc())
                    .first()
                )
                if other:
                    other.is_default = 1
            row.is_default = 0

    db.commit()
    db.refresh(row)
    return success(AddressOut.model_validate(row).model_dump(), "更新成功")


@router.put("/{address_id}/default")
def set_default_address(
    address_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """设为默认地址"""
    row = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not row:
        return error("地址不存在", 404)

    _clear_default(db, user.id, exclude_id=row.id)
    row.is_default = 1
    db.commit()
    db.refresh(row)
    return success(AddressOut.model_validate(row).model_dump(), "已设为默认地址")


@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """删除收货地址"""
    row = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not row:
        return error("地址不存在", 404)

    was_default = row.is_default == 1
    db.delete(row)
    db.commit()

    if was_default:
        other = (
            db.query(Address)
            .filter(Address.user_id == user.id)
            .order_by(Address.id.desc())
            .first()
        )
        if other:
            other.is_default = 1
            db.commit()

    return success(None, "删除成功")
