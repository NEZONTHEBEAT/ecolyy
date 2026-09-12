"""Small shared helpers used across services/routers."""
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def to_object_id(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise ValueError(f"Invalid ObjectId: {id_str}")
    return ObjectId(id_str)


def serialize_doc(doc: dict) -> dict:
    """Convert a Mongo document into a JSON-safe dict (str id, iso dates)."""
    if doc is None:
        return doc
    out: dict[str, Any] = {}
    for key, value in doc.items():
        if key == "_id":
            out["id"] = str(value)
        elif isinstance(value, ObjectId):
            out[key] = str(value)
        elif isinstance(value, datetime):
            out[key] = value.isoformat()
        elif isinstance(value, list):
            out[key] = [serialize_doc(v) if isinstance(v, dict) else v for v in value]
        elif isinstance(value, dict):
            out[key] = serialize_doc(value)
        else:
            out[key] = value
    return out


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
