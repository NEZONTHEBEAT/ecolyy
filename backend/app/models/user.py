"""
Internal representation of a user document as stored in MongoDB.
These are plain dicts in practice (Motor works with dicts), but this
class documents the shape and gives IDE/type-checker support when built.
"""
from datetime import datetime, timezone
from typing import Optional


class UserModel:
    """
    Collection: users
    {
      _id, name, email, phone, password_hash (None if Google-only),
      google_id, role ("user" | "admin"), is_verified, is_active,
      avatar_url, points, created_at, updated_at
    }
    """

    collection_name = "users"

    @staticmethod
    def new(
        name: str,
        email: str,
        phone: Optional[str] = None,
        password_hash: Optional[str] = None,
        google_id: Optional[str] = None,
        role: str = "user",
    ) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "name": name,
            "email": email.lower(),
            "phone": phone,
            "password_hash": password_hash,
            "google_id": google_id,
            "role": role,
            "is_verified": google_id is not None,
            "is_active": True,
            "avatar_url": None,
            "points": 0,
            "created_at": now,
            "updated_at": now,
        }
