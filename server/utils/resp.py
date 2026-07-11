"""
统一响应格式模块
"""

from typing import Any


def success(data: Any = None, msg: str = "操作成功") -> dict:
    """
    返回成功响应
    :param data: 响应数据
    :param msg: 提示信息
    :return: 统一格式的成功响应
    """
    return {"code": 200, "msg": msg, "data": data}


def error(msg: str = "操作失败", code: int = 400) -> dict:
    """
    返回错误响应
    :param msg: 错误信息
    :param code: 错误码
    :return: 统一格式的错误响应
    """
    return {"code": code, "msg": msg, "data": None}


def page_result(items: list, total: int, page: int, page_size: int) -> dict:
    """
    返回分页结果
    :param items: 数据列表
    :param total: 总记录数
    :param page: 当前页码
    :param page_size: 每页大小
    :return: 分页响应数据
    """
    return {
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
