"""Data-access layer for the pickups collection."""
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.helpers import to_object_id, utcnow


class PickupRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["pickups"]

    async def create(self, data: dict) -> dict:
        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return data

    async def get_by_id(self, pickup_id: str) -> dict | None:
        return await self.collection.find_one({"_id": to_object_id(pickup_id)})

    async def list_for_user(self, user_id: str, status: str | None = None) -> list[dict]:
        query: dict = {"user_id": user_id}
        if status:
            query["status"] = status
        cursor = self.collection.find(query).sort("created_at", -1)
        return [doc async for doc in cursor]

    async def list_for_partner(self, partner_id: str, status: str | None = None) -> list[dict]:
        query: dict = {"partner_id": partner_id}
        if status:
            query["status"] = status
        cursor = self.collection.find(query).sort("created_at", -1)
        return [doc async for doc in cursor]

    async def list_unassigned(self) -> list[dict]:
        cursor = self.collection.find({"status": "pending", "partner_id": None}).sort("scheduled_date", 1)
        return [doc async for doc in cursor]

    async def list_all(self, status: str | None = None, skip: int = 0, limit: int = 50) -> list[dict]:
        query = {"status": status} if status else {}
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        return [doc async for doc in cursor]

    async def count_all(self) -> int:
        return await self.collection.count_documents({})

    async def count_by_status(self) -> dict:
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        out = {}
        async for row in self.collection.aggregate(pipeline):
            out[row["_id"]] = row["count"]
        return out

    async def update_status(self, pickup_id: str, status: str, actor_id: str, extra: dict | None = None) -> None:
        update: dict = {"$set": {"status": status, "updated_at": utcnow()}}
        if extra:
            update["$set"].update(extra)
        update["$push"] = {"timeline": {"status": status, "at": utcnow(), "by": actor_id}}
        await self.collection.update_one({"_id": to_object_id(pickup_id)}, update)

    async def assign_partner(self, pickup_id: str, partner_id: str, actor_id: str) -> None:
        await self.collection.update_one(
            {"_id": to_object_id(pickup_id)},
            {
                "$set": {"partner_id": partner_id, "status": "assigned", "updated_at": utcnow()},
                "$push": {"timeline": {"status": "assigned", "at": utcnow(), "by": actor_id}},
            },
        )
