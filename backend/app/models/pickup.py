"""
Collection: pickups
{
  _id, user_id, partner_id (nullable until assigned), institution_id (nullable),
  waste_category, estimated_weight_kg, actual_weight_kg (nullable),
  address_id, address_snapshot, scheduled_date, scheduled_slot,
  status: "pending" | "assigned" | "in_progress" | "completed" | "cancelled" | "disputed",
  points_awarded, wallet_amount_awarded, notes, timeline: [ {status, at, by} ],
  created_at, updated_at
}
"""
from datetime import datetime, timezone
from typing import Optional


class PickupModel:
    collection_name = "pickups"

    STATUSES = ["pending", "assigned", "in_progress", "completed", "cancelled", "disputed"]

    @staticmethod
    def new(
        user_id: str,
        waste_category: str,
        estimated_weight_kg: float,
        address_id: str,
        address_snapshot: dict,
        scheduled_date: str,
        scheduled_slot: str,
        institution_id: Optional[str] = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "user_id": user_id,
            "partner_id": None,
            "institution_id": institution_id,
            "waste_category": waste_category,
            "estimated_weight_kg": estimated_weight_kg,
            "actual_weight_kg": None,
            "address_id": address_id,
            "address_snapshot": address_snapshot,
            "scheduled_date": scheduled_date,
            "scheduled_slot": scheduled_slot,
            "status": "pending",
            "points_awarded": 0,
            "wallet_amount_awarded": 0.0,
            "notes": None,
            "timeline": [{"status": "pending", "at": now, "by": user_id}],
            "created_at": now,
            "updated_at": now,
        }
