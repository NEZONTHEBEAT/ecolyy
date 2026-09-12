"""Data-access layer for the users collection."""
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.helpers import to_object_id


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def get_by_email(self, email: str) -> dict | None:
        return await self.collection.find_one({"email": email.lower()})

    async def get_by_id(self, user_id: str) -> dict | None:
        return await self.collection.find_one({"_id": to_object_id(user_id)})

    async def get_by_google_id(self, google_id: str) -> dict | None:
        return await self.collection.find_one({"google_id": google_id})

    async def create(self, data: dict) -> dict:
        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return data

    async def update(self, user_id: str, updates: dict) -> None:
        await self.collection.update_one({"_id": to_object_id(user_id)}, {"$set": updates})

    async def increment_points(self, user_id: str, delta: int) -> None:
        await self.collection.update_one({"_id": to_object_id(user_id)}, {"$inc": {"points": delta}})

    async def list_all(self, skip: int = 0, limit: int = 50, search: str | None = None) -> list[dict]:
        query = {}
        if search:
            query = {"$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
            ]}
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        return [doc async for doc in cursor]

    async def count_all(self) -> int:
        return await self.collection.count_documents({})

    async def set_active(self, user_id: str, is_active: bool) -> None:
        await self.collection.update_one({"_id": to_object_id(user_id)}, {"$set": {"is_active": is_active}})
