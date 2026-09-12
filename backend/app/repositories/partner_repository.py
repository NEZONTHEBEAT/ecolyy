"""Data-access layer for the partners collection."""
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.helpers import to_object_id


class PartnerRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["partners"]

    async def get_by_email(self, email: str) -> dict | None:
        return await self.collection.find_one({"email": email.lower()})

    async def get_by_id(self, partner_id: str) -> dict | None:
        return await self.collection.find_one({"_id": to_object_id(partner_id)})

    async def create(self, data: dict) -> dict:
        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return data

    async def list_all(self, skip: int = 0, limit: int = 50, verified_only: bool = False) -> list[dict]:
        query = {"is_verified": True} if verified_only else {}
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        return [doc async for doc in cursor]

    async def set_verified(self, partner_id: str, verified: bool) -> None:
        await self.collection.update_one({"_id": to_object_id(partner_id)}, {"$set": {"is_verified": verified}})

    async def set_active(self, partner_id: str, is_active: bool) -> None:
        await self.collection.update_one({"_id": to_object_id(partner_id)}, {"$set": {"is_active": is_active}})

    async def increment_stats(self, partner_id: str, pickups_delta: int = 0, earnings_delta: float = 0.0) -> None:
        await self.collection.update_one(
            {"_id": to_object_id(partner_id)},
            {"$inc": {"total_pickups": pickups_delta, "earnings_total": earnings_delta}},
        )
