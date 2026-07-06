"""
AI智能客服聊天路由
支持 REST 阻塞式接口 + WebSocket 流式输出
"""
import json
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from models.user import User
from schemas.schemas import ChatRequest, ChatMessageOut
from services.ai_service import ai_service
from utils.deps import get_current_user
from utils.resp import success, error

router = APIRouter(prefix="/api/chat", tags=["AI智能客服"])


@router.post("/send")
def send_message(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    发送消息给AI智能客服(RAG增强)-阻塞式，一次性返回完整回复
    """
    if not req.message.strip():
        return error("消息不能为空")

    try:
        result = ai_service.chat(db, user.id, req.message, req.session_id)
        return success({
            "session_id": result["session_id"],
            "answer": result["answer"],
            "messages": [ChatMessageOut.model_validate(m).model_dump() for m in result["messages"]],
            "sources": result["sources"],
            "recommended_products": result.get("recommended_products", []),
        })
    except Exception as e:
        return error(f"AI服务异常: {str(e)}", 500)


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    """
    WebSocket 流式聊天接口

    协议：
    1. 客户端连接时通过 query 参数传递 token: ?token=xxx
    2. 客户端发送 JSON: {"message": "...", "session_id": "..."}
    3. 服务端逐 token 推送 JSON（每行一个完整 JSON 对象）：
       - {"type": "session_id", "session_id": "..."}
       - {"type": "sources", "sources": [...]}    （检索来源）
       - {"type": "content", "content": "..."}   （可能多条）
       - {"type": "done", "answer": "完整回复"}
       - {"type": "error", "message": "错误信息"}
    4. 消息推送完毕后连接保持，可继续发送下一条消息
    """
    await websocket.accept()

    # 通过 query 参数认证用户
    token = None
    try:
        token = websocket.query_params.get("token", "")
        if not token:
            await websocket.send_text(json.dumps({"type": "error", "message": "缺少认证token"}, ensure_ascii=False))
            await websocket.close()
            return
    except Exception:
        pass

    # 验证 token 获取用户
    current_user = None
    db = SessionLocal()
    try:
        from utils.security import decode_access_token
        payload = decode_access_token(token)
        if payload and payload.get("type") == "user":
            user_id = int(payload.get("sub"))
            current_user = db.query(User).filter(User.id == user_id, User.status == 1).first()
        if not current_user:
            await websocket.send_text(json.dumps({"type": "error", "message": "认证失败或用户不存在"}, ensure_ascii=False))
            await websocket.close()
            return
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "message": f"认证异常: {str(e)}"}, ensure_ascii=False))
        await websocket.close()
        return

    # 消息循环
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "消息格式错误，请发送JSON"}, ensure_ascii=False))
                continue

            message = data.get("message", "").strip()
            if not message:
                await websocket.send_text(json.dumps({"type": "error", "message": "消息不能为空"}, ensure_ascii=False))
                continue
            if len(message) > 1000:
                await websocket.send_text(json.dumps({"type": "error", "message": "消息不能超过1000字"}, ensure_ascii=False))
                continue

            session_id = data.get("session_id")
            if session_id and len(str(session_id)) > 64:
                await websocket.send_text(json.dumps({"type": "error", "message": "会话ID格式错误"}, ensure_ascii=False))
                continue

            try:
                async for chunk in ai_service.chat_stream(db, current_user.id, message, session_id):
                    await websocket.send_text(chunk)
                    # 更新 session_id（首条消息返回后）
                    if '"type":"session_id"' in chunk or '"type": "session_id"' in chunk:
                        parsed = json.loads(chunk)
                        session_id = parsed.get("session_id", session_id)
            except Exception as e:
                await websocket.send_text(json.dumps({"type": "error", "message": f"AI服务异常: {str(e)}"}, ensure_ascii=False))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False))
        except Exception:
            pass
    finally:
        db.close()


@router.get("/history")
def chat_history(
    session_id: str = Query(..., description="会话ID"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    获取聊天历史记录
    """
    messages = ai_service.get_chat_history(db, user.id, session_id)
    return success([ChatMessageOut.model_validate(m).model_dump() for m in messages])
