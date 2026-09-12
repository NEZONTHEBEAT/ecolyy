"""Data-access layer for rewards and redemptions."""
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.helpers import to_object_id


class RewardRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.rewards = db["rewards"]
        self.redemptions = db["reward_redemptions"]

    async def list_active(self) -> list[dict]:
        cursor = self.rewards.find({"is_active": True}).sort("points_cost", 1)
        return [doc async for doc in cursor]

    async def get_by_id(self, reward_id: str) -> dict | None:
        return await self.rewards.find_one({"_id": to_object_id(reward_id)})

    async def create(self, data: dict) -> dict:
        result = await self.rewards.insert_one(data)
        data["_id"] = result.inserted_id
        return data

    async def decrement_stock(self, reward_id: str) -> None:
        await self.rewards.update_one(
            {"_id": to_object_id(reward_id), "stock": {"$gt": 0}},
            {"$inc": {"stock": -1}},
        )

    async def create_redemption(self, data: dict) -> dict:
        result = await self.redemptions.insert_one(data)
        data["_id"] = result.inserted_id
        return data

    async def list_redemptions_for_user(self, user_id: str) -> list[dict]:
        cursor = self.redemptions.find({"user_id": user_id}).sort("redeemed_at", -1)
        return [doc async for doc in cursor]
