from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from database import get_db
import models
from auth import get_current_user

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


class RoomCreate(BaseModel):
    name: str


class RoomOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    username: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[RoomOut])
def list_rooms(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Room).order_by(models.Room.name).all()


@router.post("", response_model=RoomOut)
def create_room(payload: RoomCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    existing = db.query(models.Room).filter(models.Room.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Room already exists")

    room = models.Room(name=payload.name, created_by=user.id)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/{room_id}/messages", response_model=List[MessageOut])
def get_messages(room_id: int, limit: int = 50, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    msgs = (
        db.query(models.Message)
        .filter(models.Message.room_id == room_id)
        .order_by(models.Message.created_at.desc())
        .limit(limit)
        .all()
    )
    msgs.reverse()

    return [
        MessageOut(id=m.id, username=m.user.username, content=m.content, created_at=m.created_at)
        for m in msgs
    ]
