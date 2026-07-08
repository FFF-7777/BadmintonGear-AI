"""
文件上传路由
统一上传图片/文件到 uploads 目录，带文件头魔术字节校验。
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File

from config import UPLOAD_DIR, PRODUCT_DIR, BANNER_DIR, AVATAR_DIR
from utils.deps import get_current_admin, get_current_user
from utils.resp import success, error

router = APIRouter(prefix="/api/upload", tags=["文件上传"])

# 图片文件头魔术字节（用于深度校验，防止伪造 content_type）
_IMAGE_SIGNATURES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/gif": [b"GIF87a", b"GIF89a"],
    "image/webp": [b"RIFF"],
}
_ALLOWED_MIMES = set(_IMAGE_SIGNATURES.keys())


def _validate_image_signature(content: bytes, declared_mime: str) -> bool:
    """校验文件头魔术字节，防止伪造 content_type 上传非图片文件。"""
    if declared_mime not in _IMAGE_SIGNATURES or not content:
        return False
    for sig in _IMAGE_SIGNATURES[declared_mime]:
        if content.startswith(sig):
            # WebP 还需校验偏移 8 处为 WEBP
            if declared_mime == "image/webp":
                return len(content) >= 12 and content[8:12] == b"WEBP"
            return True
    return False


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
    if file.content_type not in _ALLOWED_MIMES:
        return error("仅支持jpg/png/gif/webp格式图片")

    content = await file.read()
    if not _validate_image_signature(content, file.content_type):
        return error("文件内容与声明类型不匹配，疑似伪造文件")

    dir_map = {"product": PRODUCT_DIR, "banner": BANNER_DIR, "avatar": AVATAR_DIR}
    save_dir = dir_map.get(type, UPLOAD_DIR)
    save_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix or ".jpg"
    save_name = f"{uuid.uuid4().hex}{ext}"
    save_path = save_dir / save_name

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
    if file.content_type not in _ALLOWED_MIMES:
        return error("仅支持jpg/png/gif/webp格式图片")

    content = await file.read()
    if not _validate_image_signature(content, file.content_type):
        return error("文件内容与声明类型不匹配，疑似伪造文件")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix or ".jpg"
    save_name = f"{uuid.uuid4().hex}{ext}"
    save_path = AVATAR_DIR / save_name

    with open(save_path, "wb") as f:
        f.write(content)

    url_path = f"/uploads/avatar/{save_name}"
    return success({"url": url_path, "path": str(save_path).replace("\\", "/")}, "上传成功")
