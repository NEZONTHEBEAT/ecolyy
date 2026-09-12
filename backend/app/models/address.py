"""
Collection: addresses
{ _id, user_id, label, line1, line2, city, state, pincode, lat, lng,
  is_default, created_at }
"""
from datetime import datetime, timezone
from typing import Optional


class AddressModel:
    collection_name = "addresses"

    @staticmethod
    def new(
        user_id: str, label: str, line1: str, city: str, state: str, pincode: str,
        line2: Optional[str] = None, lat: Optional[float] = None, lng: Optional[float] = None,
        is_default: bool = False,
    ) -> dict:
        return {
            "user_id": user_id,
            "label": label,
            "line1": line1,
            "line2": line2,
            "city": city,
            "state": state,
            "pincode": pincode,
            "lat": lat,
            "lng": lng,
            "is_default": is_default,
            "created_at": datetime.now(timezone.utc),
        }
