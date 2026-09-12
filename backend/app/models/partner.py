"""
Collection: partners
{
  _id, name, email, phone, password_hash, vehicle_type, service_areas: [str],
  documents: [ {type, url, verified} ], is_verified, is_active,
  rating_avg, total_pickups, earnings_total, created_at, updated_at
}
"""
from datetime import datetime, timezone
from typing import Optional


class PartnerModel:
    collection_name = "partners"

    @staticmethod
    def new(name: str, email: str, phone: str, password_hash: str, vehicle_type: Optional[str] = None) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "name": name,
            "email": email.lower(),
            "phone": phone,
            "password_hash": password_hash,
            "vehicle_type": vehicle_type,
            "service_areas": [],
            "documents": [],
            "is_verified": False,
            "is_active": True,
            "rating_avg": 0.0,
            "total_pickups": 0,
            "earnings_total": 0.0,
            "created_at": now,
            "updated_at": now,
        }
