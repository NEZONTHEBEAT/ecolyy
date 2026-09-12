"""
Collection: notifications
{ _id, user_id, role, title, message, is_read, type, created_at }
"""
from datetime import datetime, timezone


class NotificationModel:
    collection_name = "notifications"

    @staticmethod
    def new(user_id: str, role: str, title: str, message: str, notif_type: str = "info") -> dict:
        return {
            "user_id": user_id,
            "role": role,
            "title": title,
            "message": message,
            "is_read": False,
            "type": notif_type,
            "created_at": datetime.now(timezone.utc),
        }
