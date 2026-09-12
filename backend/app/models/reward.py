"""
Collection: rewards           -> catalog of redeemable rewards
Collection: reward_redemptions -> per-user redemption history

reward: { _id, title, description, points_cost, stock, is_active, image_url, created_at }
redemption: { _id, user_id, reward_id, points_spent, status, redeemed_at }
"""
from datetime import datetime, timezone


class RewardModel:
    collection_name = "rewards"

    @staticmethod
    def new(title: str, description: str, points_cost: int, stock: int = -1, image_url: str | None = None) -> dict:
        return {
            "title": title,
            "description": description,
            "points_cost": points_cost,
            "stock": stock,  # -1 = unlimited
            "is_active": True,
            "image_url": image_url,
            "created_at": datetime.now(timezone.utc),
        }


class RewardRedemptionModel:
    collection_name = "reward_redemptions"

    @staticmethod
    def new(user_id: str, reward_id: str, points_spent: int) -> dict:
        return {
            "user_id": user_id,
            "reward_id": reward_id,
            "points_spent": points_spent,
            "status": "pending",
            "redeemed_at": datetime.now(timezone.utc),
        }
