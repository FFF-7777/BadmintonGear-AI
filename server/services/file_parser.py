"""
文件解析服务
支持txt、doc、pdf、markdown四种格式的知识库文件解析
"""
import re
from pathlib import Path


# PDF/DOCX 等二进制文档解析后常残留孤立的 UTF-16 代理码点（lone surrogate，
# 如 \udc89），它们无法被 UTF-8 编码，会在后续 json.dumps / .encode("utf-8") 时
# 触发 UnicodeEncodeError。在解析出口统一替换为 U+FFFD，从源头切断。
_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")


def _sanitize(text: str) -> str:
    return _SURROGATE_RE.sub("\ufffd", text) if text else text


def parse_txt(file_path: str) -> str:
    """
    解析TXT文本文件
    :param file_path: 文件路径
    :return: 文本内容
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def parse_doc(file_path: str) -> str:
    """
    解析DOC/DOCX文档文件
    :param file_path: 文件路径
    :return: 文本内容
    """
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def parse_pdf(file_path: str) -> str:
    """
    解析PDF文件
    :param file_path: 文件路径
    :return: 文本内容
    """
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    texts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            texts.append(text)
    return "\n".join(texts)


def parse_markdown(file_path: str) -> str:
    """
    解析Markdown文件
    :param file_path: 文件路径
    :return: 文本内容
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    # 保留原始markdown文本用于RAG检索
    return content


def parse_file(file_path: str, file_type: str) -> str:
    """
    根据文件类型解析文件内容
    :param file_path: 文件路径
    :param file_type: 文件类型(txt/doc/pdf/markdown)
    :return: 解析后的文本内容
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    type_map = {
        "txt": parse_txt,
        "doc": parse_doc,
        "docx": parse_doc,
        "pdf": parse_pdf,
        "markdown": parse_markdown,
        "md": parse_markdown,
    }

    parser = type_map.get(file_type.lower())
    if not parser:
        raise ValueError(f"不支持的文件类型: {file_type}")

    raw = parser(file_path)
    return _sanitize(raw)


def get_file_type(filename: str) -> str:
    """
    根据文件名获取文件类型
    :param filename: 文件名
    :return: 文件类型
    """
    ext = Path(filename).suffix.lower().lstrip(".")
    type_map = {"txt": "txt", "doc": "doc", "docx": "docx", "pdf": "pdf", "md": "markdown", "markdown": "markdown"}
    return type_map.get(ext, ext)
