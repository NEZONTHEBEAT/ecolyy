"""
/api/v1/institutions — institution dashboard: locations, pickups, reports, certificates.
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.permissions import require_institution
from app.repositories.pickup_repository import PickupRepository
from app.utils.helpers import serialize_doc, to_object_id

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.get("/me")
async def get_my_institution_profile(current_user: dict = Depends(require_institution)):
    return serialize_doc(current_user)


@router.get("/me/pickups")
async def get_institution_pickups(current_user: dict = Depends(require_institution),
                                   db: AsyncIOMotorDatabase = Depends(get_database)):
    cursor = db["pickups"].find({"institution_id": current_user["_id"]}).sort("created_at", -1)
    return [serialize_doc(doc) async for doc in cursor]


@router.post("/me/locations")
async def add_location(payload: dict, current_user: dict = Depends(require_institution),
                        db: AsyncIOMotorDatabase = Depends(get_database)):
    location = {
        "label": payload.get("label"), "address": payload.get("address"),
        "lat": payload.get("lat"), "lng": payload.get("lng"),
    }
    await db["institutions"].update_one({"_id": to_object_id(current_user["_id"])}, {"$push": {"locations": location}})
    updated = await db["institutions"].find_one({"_id": to_object_id(current_user["_id"])})
    return serialize_doc(updated)


@router.get("/me/reports")
async def get_impact_report(current_user: dict = Depends(require_institution),
                             db: AsyncIOMotorDatabase = Depends(get_database)):
    """Aggregate recycled weight / pickups for this institution — powers reports.html & certificates.html."""
    pipeline = [
        {"$match": {"institution_id": current_user["_id"], "status": "completed"}},
        {"$group": {
            "_id": "$waste_category",
            "total_weight_kg": {"$sum": "$actual_weight_kg"},
            "pickups": {"$sum": 1},
        }},
    ]
    breakdown = [row async for row in db["pickups"].aggregate(pipeline)]
    total_weight = sum(row["total_weight_kg"] or 0 for row in breakdown)
    total_pickups = sum(row["pickups"] for row in breakdown)
    return {"total_weight_kg": total_weight, "total_pickups": total_pickups, "by_category": breakdown}
