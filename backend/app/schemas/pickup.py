from typing import Literal, Optional

from pydantic import BaseModel, Field


class PickupCreate(BaseModel):
    waste_category: str
    estimated_weight_kg: float = Field(gt=0)
    address_id: str
    scheduled_date: str  # "YYYY-MM-DD"
    scheduled_slot: str  # e.g. "10:00-12:00"
    institution_id: Optional[str] = None
    notes: Optional[str] = None


class PickupStatusUpdate(BaseModel):
    status: Literal["assigned", "in_progress", "completed", "cancelled", "disputed"]
    actual_weight_kg: Optional[float] = None
    notes: Optional[str] = None


class PickupAssign(BaseModel):
    partner_id: str


class PickupOut(BaseModel):
    id: str
    user_id: str
    partner_id: Optional[str]
    waste_category: str
    estimated_weight_kg: float
    actual_weight_kg: Optional[float]
    address_snapshot: dict
    scheduled_date: str
    scheduled_slot: str
    status: str
    points_awarded: int
    wallet_amount_awarded: float
    created_at: str
