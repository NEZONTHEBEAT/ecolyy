"""Creates in-app notifications. Push/SMS/email fan-out can be added later."""
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.notification import NotificationModel


async def notify(db: AsyncIOMotorDatabase, user_id: str, role: str, title: str, message: str, notif_type: str = "info") -> None:
    doc = NotificationModel.new(user_id, role, title, message, notif_type)
    await db["notifications"].insert_one(doc)


async def list_for_user(db: AsyncIOMotorDatabase, user_id: str, unread_only: bool = False) -> list[dict]:
    query: dict = {"user_id": user_id}
    if unread_only:
        query["is_read"] = False
    cursor = db["notifications"].find(query).sort("created_at", -1).limit(100)
    return [doc async for doc in cursor]


async def mark_read(db: AsyncIOMotorDatabase, notification_id: str) -> None:
    from app.utils.helpers import to_object_id
    await db["notifications"].update_one({"_id": to_object_id(notification_id)}, {"$set": {"is_read": True}})
