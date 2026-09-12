"""Reward catalog + redemption logic (spends points, tracks stock)."""
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.reward import RewardRedemptionModel
from app.repositories.reward_repository import RewardRepository
from app.repositories.user_repository import UserRepository


async def redeem_reward(db: AsyncIOMotorDatabase, user_id: str, reward_id: str) -> dict:
    reward_repo = RewardRepository(db)
    user_repo = UserRepository(db)

    reward = await reward_repo.get_by_id(reward_id)
    if not reward or not reward.get("is_active"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reward not found")
    if reward["stock"] == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This reward is out of stock")

    user = await user_repo.get_by_id(user_id)
    if not user or user.get("points", 0) < reward["points_cost"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not enough points")

    await user_repo.increment_points(user_id, -reward["points_cost"])
    if reward["stock"] > 0:
        await reward_repo.decrement_stock(reward_id)

    redemption = RewardRedemptionModel.new(user_id, reward_id, reward["points_cost"])
    return await reward_repo.create_redemption(redemption)
