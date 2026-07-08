"""
安全工具模块
提供 bcrypt 密码哈希和 JWT 令牌生成/验证。

安全说明：
- 密码使用 bcrypt（带盐），替代原 MD5 方案。
- 旧的 32 位 hex MD5 密码可通过 is_legacy_password() 识别，由 bootstrap 自动迁移。
- JWT SECRET_KEY 必须由环境变量提供，无默认值——启动时缺失即报错。
"""
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS

_BCRYPT_PREFIX = "$2"
_MD5_HEX_LEN = 32
_MD5_CHARSET = set("0123456789abcdef")


def hash_password(plain: str) -> str:
    """
    使用 bcrypt 哈希密码（自动加盐）。
    :param plain: 明文密码
    :return: bcrypt 哈希字符串
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配（仅接受 bcrypt 格式）。
    :param plain_password: 明文密码
    :param hashed_password: bcrypt 哈希字符串
    :return: 是否匹配
    """
    if not hashed_password or not hashed_password.startswith(_BCRYPT_PREFIX):
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def is_legacy_password(hashed: str) -> bool:
    """
    判断是否为旧 MD5 格式密码（32 位 hex），用于 bootstrap 自动迁移。
    迁移完成后旧密码不再被 verify_password 接受。
    """
    if not hashed or hashed.startswith(_BCRYPT_PREFIX):
        return False
    return len(hashed) == _MD5_HEX_LEN and set(hashed.lower()).issubset(_MD5_CHARSET)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌
    :param data: 令牌载荷数据
    :param expires_delta: 过期时间增量
    :return: JWT 令牌字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码 JWT 访问令牌
    :param token: JWT 令牌字符串
    :return: 解码后的载荷数据，失败返回 None
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
