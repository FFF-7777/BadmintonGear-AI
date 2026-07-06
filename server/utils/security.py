"""
安全工具模块
提供MD5加密和JWT令牌生成/验证
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS


def md5_hash(text: str) -> str:
    """
    对字符串进行MD5加密
    :param text: 原始字符串
    :return: MD5哈希值
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配
    :param plain_password: 明文密码
    :param hashed_password: MD5加密后的密码
    :return: 是否匹配
    """
    return md5_hash(plain_password) == hashed_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    :param data: 令牌载荷数据
    :param expires_delta: 过期时间增量
    :return: JWT令牌字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码JWT访问令牌
    :param token: JWT令牌字符串
    :return: 解码后的载荷数据，失败返回None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
