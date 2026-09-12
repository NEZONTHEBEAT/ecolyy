"""
Collection: institutions
{
  _id, name, email, phone, password_hash, type (school/college/office/society),
  locations: [ {label, address, lat, lng} ], is_verified, is_active,
  created_at, updated_at
}
"""
from datetime import datetime, timezone
from typing import Optional


class InstitutionModel:
    collection_name = "institutions"

    @staticmethod
    def new(name: str, email: str, phone: str, password_hash: str, inst_type: Optional[str] = None) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "name": name,
            "email": email.lower(),
            "phone": phone,
            "password_hash": password_hash,
            "type": inst_type,
            "locations": [],
            "is_verified": False,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
