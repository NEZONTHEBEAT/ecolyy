"""
/api/v1/rewards — browse the reward catalog and redeem points.
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.permissions import require_user
from app.repositories.reward_repository import RewardRepository
from app.schemas.reward import RedeemRequest
from app.services import reward_service
from app.utils.helpers import serialize_doc

router = APIRouter(prefix="/rewards", tags=["Rewards"])


@router.get("")
async def list_rewards(db: AsyncIOMotorDatabase = Depends(get_database)):
    repo = RewardRepository(db)
    items = await repo.list_active()
    return [serialize_doc(i) for i in items]


@router.post("/redeem")
async def redeem_reward(payload: RedeemRequest, current_user: dict = Depends(require_user),
                         db: AsyncIOMotorDatabase = Depends(get_database)):
    redemption = await reward_service.redeem_reward(db, current_user["_id"], payload.reward_id)
    return serialize_doc(redemption)


@router.get("/me/history")
async def my_redemptions(current_user: dict = Depends(require_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    repo = RewardRepository(db)
    items = await repo.list_redemptions_for_user(current_user["_id"])
    return [serialize_doc(i) for i in items]
