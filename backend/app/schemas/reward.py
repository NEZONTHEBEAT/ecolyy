from typing import Optional

from pydantic import BaseModel, Field


class RewardCreate(BaseModel):
    title: str
    description: str
    points_cost: int = Field(gt=0)
    stock: int = -1
    image_url: Optional[str] = None


class RewardOut(RewardCreate):
    id: str
    is_active: bool


class RedeemRequest(BaseModel):
    reward_id: str
