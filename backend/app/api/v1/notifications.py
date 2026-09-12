"""
/api/v1/notifications — in-app notifications for the logged-in user
(any role: user, partner, institution, admin — all share this router
since notifications.user_id just matches whichever account is logged in).
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.permissions import get_current_user
from app.services import notification_service
from app.utils.helpers import serialize_doc

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/me")
async def get_my_notifications(unread_only: bool = False, current_user: dict = Depends(get_current_user),
                                db: AsyncIOMotorDatabase = Depends(get_database)):
    items = await notification_service.list_for_user(db, current_user["_id"], unread_only)
    return [serialize_doc(i) for i in items]


@router.patch("/me/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user),
                                  db: AsyncIOMotorDatabase = Depends(get_database)):
    await notification_service.mark_read(db, notification_id)
    return {"message": "Marked as read"}
