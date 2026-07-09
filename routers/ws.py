from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from database import SessionLocal
import models
from auth import get_user_from_token_str
from connection_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def dm_ws(websocket: WebSocket, token: str = Query(...)):
    db: Session = SessionLocal()
    user = get_user_from_token_str(token, db)

    if not user:
        await websocket.close(code=4001)
        db.close()
        return

    await manager.connect(user.id, websocket)
    await manager.broadcast_all({
        "type": "presence",
        "online_user_ids": manager.online_user_ids(),
    })

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            to_user_id = data.get("to")
            if not content or not to_user_id:
                continue

            recipient = db.query(models.User).filter(models.User.id == to_user_id).first()
            if not recipient:
                continue

            msg = models.DirectMessage(sender_id=user.id, recipient_id=to_user_id, content=content)
            db.add(msg)
            db.commit()
            db.refresh(msg)

            payload = {
                "type": "message",
                "id": msg.id,
                "sender_id": user.id,
                "sender_username": user.username,
                "recipient_id": to_user_id,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }

            # deliver to recipient if online, and echo back to sender (for multi-tab sync)
            await manager.send_to_user(to_user_id, payload)
            await manager.send_to_user(user.id, payload)

    except WebSocketDisconnect:
        manager.disconnect(user.id)
        await manager.broadcast_all({
            "type": "presence",
            "online_user_ids": manager.online_user_ids(),
        })
    finally:
        db.close()