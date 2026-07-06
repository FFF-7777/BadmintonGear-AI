"""
文件上传路由
统一上传图片/文件到 D:/uploads14
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File
from config import UPLOAD_DIR, PRODUCT_DIR, BANNER_DIR, AVATAR_DIR
from utils.deps import get_current_admin, get_current_user
from utils.resp import success, error

router = APIRouter(prefix="/api/upload", tags=["文件上传"])


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    type: str = "product",
    admin=Depends(get_current_admin),
):
    """
    上传图片文件
    :param file: 图片文件
    :param type: 类型 product/banner/avatar
    :return: 图片访问路径
    """
    allowed = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed:
        return error("仅支持jpg/png/gif/webp格式图片")

    dir_map = {"product": PRODUCT_DIR, "banner": BANNER_DIR, "avatar": AVATAR_DIR}
    save_dir = dir_map.get(type, UPLOAD_DIR)
    save_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix or ".jpg"
    save_name = f"{uuid.uuid4().hex}{ext}"
    save_path = save_dir / save_name

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    url_path = f"/uploads/{type}/{save_name}" if type in dir_map else f"/uploads/{save_name}"
    return success({"url": url_path, "path": str(save_path).replace("\\", "/")}, "上传成功")


@router.post("/user/avatar")
async def upload_user_avatar(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """
    用户上传头像(小程序)
    :param file: 图片文件
    :return: 头像访问路径
    """
    allowed = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed:
        return error("仅支持jpg/png/gif/webp格式图片")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix or ".jpg"
    save_name = f"{uuid.uuid4().hex}{ext}"
    save_path = AVATAR_DIR / save_name

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    url_path = f"/uploads/avatar/{save_name}"
    return success({"url": url_path, "path": str(save_path).replace("\\", "/")}, "上传成功")
