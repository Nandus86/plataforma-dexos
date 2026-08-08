from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class NotificationSend(BaseModel):
    recipient_id: UUID
    title: str
    message: str

@router.post("/send")
async def send_notification(
    data: NotificationSend,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notif = Notification(
        tenant_id=current_user.tenant_id,
        sender_id=current_user.id,
        recipient_id=data.recipient_id,
        title=data.title,
        message=data.message,
        is_read=False
    )
    db.add(notif)
    await db.commit()
    return {"detail": "Notification sent successfully"}


@router.get("/my")
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(
        select(Notification)
        .where(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    notifications = res.scalars().all()
    
    sender_ids = list(set([n.sender_id for n in notifications if n.sender_id]))
    senders = {}
    if sender_ids:
        s_res = await db.execute(select(User.id, User.name).where(User.id.in_(sender_ids)))
        for s_id, s_name in s_res.all():
            senders[s_id] = s_name

    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at,
            "sender_name": senders.get(n.sender_id, "Sistema") if n.sender_id else "Sistema"
        } for n in notifications
    ]


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.recipient_id == current_user.id)
    )
    notif = res.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notif.is_read = True
    await db.commit()
    return {"detail": "Marked as read"}
