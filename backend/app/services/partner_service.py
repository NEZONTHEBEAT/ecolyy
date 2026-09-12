"""Partner-facing business logic: verification, service areas, earnings summary."""
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.partner_repository import PartnerRepository
from app.repositories.pickup_repository import PickupRepository


async def get_earnings_summary(db: AsyncIOMotorDatabase, partner_id: str) -> dict:
    partner_repo = PartnerRepository(db)
    pickup_repo = PickupRepository(db)

    partner = await partner_repo.get_by_id(partner_id)
    completed = await db["pickups"].count_documents({"partner_id": partner_id, "status": "completed"})
    pending = await db["pickups"].count_documents({"partner_id": partner_id, "status": {"$in": ["assigned", "in_progress"]}})

    return {
        "total_earnings": partner.get("earnings_total", 0.0) if partner else 0.0,
        "total_pickups": partner.get("total_pickups", 0) if partner else 0,
        "completed_pickups": completed,
        "pending_pickups": pending,
        "rating_avg": partner.get("rating_avg", 0.0) if partner else 0.0,
    }


async def set_verification(db: AsyncIOMotorDatabase, partner_id: str, verified: bool) -> None:
    repo = PartnerRepository(db)
    await repo.set_verified(partner_id, verified)
