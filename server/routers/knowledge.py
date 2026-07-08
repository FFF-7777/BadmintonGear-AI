"""
知识库管理路由
支持txt/docx/pdf/markdown文件上传、解析、向量化
"""
import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from config import KNOWLEDGE_DIR
from database import get_db
from models.knowledge import KnowledgeFile
from schemas.schemas import KnowledgeFileOut
from services.file_parser import parse_file, get_file_type
from services.rag_pipeline import extract_model_tokens, infer_brand, infer_doc_type, infer_series
from services.vector_store import vector_store_service, safe_add_documents, safe_search, safe_delete_documents
from utils.deps import get_current_admin
from utils.resp import success, error, page_result

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])

# 允许上传的文件类型
ALLOWED_TYPES = {"txt", "docx", "pdf", "md", "markdown"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.get("/admin/list")
def knowledge_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """管理员分页查询知识库文件列表"""
    query = db.query(KnowledgeFile)
    total = query.count()
    items = query.order_by(KnowledgeFile.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return success(page_result(
        [KnowledgeFileOut.model_validate(i).model_dump() for i in items],
        total, page, page_size,
    ))


@router.post("/admin/upload")
def upload_knowledge(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    上传知识库文件并自动解析向量化
    支持格式: txt, docx, pdf, markdown
    """
    filename = (file.filename or "").strip()
    if not filename:
        return error("文件名不能为空")

    file_type = get_file_type(filename)
    if file_type not in ALLOWED_TYPES:
        return error("不支持的文件格式，仅支持 txt/docx/pdf/markdown")

    # 保存文件到 D:/uploads14/knowledge/
    ext = Path(filename).suffix
    save_name = f"{uuid.uuid4().hex}{ext}"
    save_path = KNOWLEDGE_DIR / save_name

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = save_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        save_path.unlink(missing_ok=True)
        return error("知识库文件不能超过10MB")

    # 创建数据库记录
    initial_text = filename
    model_aliases = extract_model_tokens(initial_text)
    kf = KnowledgeFile(
        file_name=filename,
        file_type=file_type,
        file_path=str(save_path).replace("\\", "/"),
        brand=infer_brand(initial_text) or None,
        series=infer_series(initial_text) or None,
        model_aliases=",".join(model_aliases) if model_aliases else None,
        doc_type=infer_doc_type(initial_text),
        file_size=file_size,
        status=0,
    )
    db.add(kf)
    db.commit()
    db.refresh(kf)

    # 解析并向量化；同步路由会由 FastAPI 在线程池执行，不阻塞事件循环。
    # 使用子进程隔离的 safe_add_documents，避免 chroma 原生崩溃拖垮服务进程。
    text = parse_file(str(save_path), file_type)
    kf.brand = infer_brand(f"{filename} {text[:2000]}") or kf.brand
    kf.series = infer_series(f"{filename} {text[:2000]}") or kf.series
    file_models = extract_model_tokens(f"{filename} {text[:2000]}")
    kf.model_aliases = ",".join(file_models) if file_models else kf.model_aliases
    kf.doc_type = infer_doc_type(f"{filename} {text[:2000]}")
    chunk_count, add_err = safe_add_documents(
        text,
        kf.id,
        kf.file_name,
        kf.file_type,
    )
    if add_err:
        kf.status = 2
        kf.chunk_count = 0
        kf.error_msg = str(add_err)[:500]
    else:
        kf.status = 1
        kf.chunk_count = chunk_count

    db.commit()
    db.refresh(kf)
    data = KnowledgeFileOut.model_validate(kf).model_dump()
    if kf.status == 2:
        return error(f"文件已保存，但向量化失败: {kf.error_msg}", 500)
    return success(data, "上传并向量化成功")


@router.post("/admin/{file_id}/vectorize")
def vectorize_knowledge(
    file_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """重新向量化知识库文件"""
    kf = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
    if not kf:
        return error("文件不存在", 404)

    try:
        text = parse_file(kf.file_path, kf.file_type)
        kf.brand = infer_brand(f"{kf.file_name} {text[:2000]}") or kf.brand
        kf.series = infer_series(f"{kf.file_name} {text[:2000]}") or kf.series
        file_models = extract_model_tokens(f"{kf.file_name} {text[:2000]}")
        kf.model_aliases = ",".join(file_models) if file_models else kf.model_aliases
        kf.doc_type = infer_doc_type(f"{kf.file_name} {text[:2000]}")
        chunk_count, add_err = safe_add_documents(
            text,
            kf.id,
            kf.file_name,
            kf.file_type,
        )
        if add_err:
            kf.status = 2
            kf.error_msg = str(add_err)[:500]
        else:
            kf.status = 1
            kf.chunk_count = chunk_count
            kf.error_msg = None
    except Exception as e:
        kf.status = 2
        kf.error_msg = str(e)[:500]

    db.commit()
    if kf.status == 2:
        return error(f"向量化失败: {kf.error_msg}", 500)
    return success(None, "向量化完成")


@router.get("/admin/search-test")
def search_test(
    query: str = Query(..., min_length=1, max_length=500),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """查看查询分析、多路召回数量和最终精排结果。"""
    try:
        result = safe_search(query)
    except Exception as e:
        return error(f"检索失败: {str(e)}", 500)

    if result.analysis is None:
        return success({
            "note": getattr(result, "note", "向量检索当前不可用（已隔离）。以下为降级信息。"),
            "route_counts": result.route_counts,
            "route_errors": result.route_errors,
            "results": [],
            "analysis": None,
        })

    return success({
        "analysis": {
            "original_query": result.analysis["original_query"],
            "expanded_query": result.analysis["expanded_query"],
            "category": result.analysis["category"],
            "queries": result.analysis["queries"],
            "scope": result.analysis.get("scope"),
            "model_tokens": result.analysis.get("model_tokens", []),
            "compare_targets": result.analysis.get("compare_targets", []),
        },
        "route_counts": result.route_counts,
        "route_errors": result.route_errors,
        "results": [
            {
                "content": document.page_content,
                "file_id": document.metadata.get("file_id"),
                "file_name": document.metadata.get("file_name"),
                "section_title": document.metadata.get("section_title"),
                "routes": document.metadata.get("retrieval_routes"),
                "score": document.metadata.get("retrieval_score"),
                "relevance": document.metadata.get("relevance_score"),
            }
            for document in result.documents
        ],
    })


@router.delete("/admin/{file_id}")
def delete_knowledge(
    file_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """删除知识库文件"""
    kf = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
    if not kf:
        return error("文件不存在", 404)

    # P1b：走子进程隔离删除，避免 chroma 原生崩溃拖死主进程；
    # 向量删除失败不阻断文件记录与磁盘清理。
    delete_err = safe_delete_documents(kf.id)
    if delete_err:
        logger.warning("向量数据删除失败（已隔离，不影响记录删除）：%s", delete_err)
    try:
        Path(kf.file_path).unlink(missing_ok=True)
    except Exception:
        pass

    db.delete(kf)
    db.commit()
    return success(None, "删除成功")
