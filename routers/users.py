from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel
from typing import List
from datetime import datetime

from database import get_db
import models
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["users"])


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class DMOut(BaseModel):
    id: int
    sender_id: int
    sender_username: str
    recipient_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.User).filter(models.User.id != user.id).order_by(models.User.username).all()


@router.get("/dm/{other_user_id}/messages", response_model=List[DMOut])
def get_dm_history(other_user_id: int, limit: int = 50, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    other = db.query(models.User).filter(models.User.id == other_user_id).first()
    if not other:
        raise HTTPException(status_code=404, detail="User not found")

    msgs = (
        db.query(models.DirectMessage)
        .filter(
            or_(
                and_(models.DirectMessage.sender_id == user.id, models.DirectMessage.recipient_id == other_user_id),
                and_(models.DirectMessage.sender_id == other_user_id, models.DirectMessage.recipient_id == user.id),
            )
        )
        .order_by(models.DirectMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    msgs.reverse()

    return [
        DMOut(
            id=m.id,
            sender_id=m.sender_id,
            sender_username=m.sender.username if m.sender_id == other_user_id else user.username,
            recipient_id=m.recipient_id,
            content=m.content,
            created_at=m.created_at,
        )
        for m in msgs
    ]