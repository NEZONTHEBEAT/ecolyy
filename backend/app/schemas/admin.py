from typing import Optional

from pydantic import BaseModel


class AdminStats(BaseModel):
    total_users: int
    total_partners: int
    total_institutions: int
    total_pickups: int
    pickups_by_status: dict
    total_points_awarded: int
    total_wallet_paid_out: float


class UserStatusUpdate(BaseModel):
    is_active: bool
    reason: Optional[str] = None


class WasteCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    points_per_kg: float
    wallet_rate_per_kg: float
    icon: Optional[str] = None
