"""
/api/v1/pickups — create & track pickups.

Supports:
- user pickup creation
- institution pickup scheduling
- user pickup tracking
- partner assigned pickup tracking
- admin partner assignment
- partner/admin status updates
- user pickup cancellation

Institution scheduling uses the institution's own embedded
locations instead of the users.addresses collection.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.permissions import (
    get_current_user,
    require_institution,
    require_partner,
    require_user,
)
from app.repositories.pickup_repository import PickupRepository
from app.schemas.pickup import (
    PickupAssign,
    PickupCreate,
    PickupStatusUpdate,
)
from app.services import pickup_service
from app.utils.helpers import serialize_doc


router = APIRouter(
    prefix="/pickups",
    tags=["Pickups"],
)


# =========================================================
# USER — CREATE PICKUP
# =========================================================

@router.post("")
async def create_pickup(
    payload: PickupCreate,
    current_user: dict = Depends(require_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Existing USER pickup creation flow.

    Uses:
        users.addresses
    """

    created = await pickup_service.create_pickup(
        db,
        current_user["_id"],
        payload,
    )

    return serialize_doc(created)


# =========================================================
# INSTITUTION — SCHEDULE PICKUP
# =========================================================

@router.post("/institution")
async def create_institution_pickup(
    payload: dict,
    current_user: dict = Depends(require_institution),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Create a pickup on behalf of an institution.

    Duplicate protection:
    The same institution cannot create another active pickup
    for the same location + waste category + scheduled date +
    scheduled slot.

    Expected payload:

    {
        "waste_category": "Paper",
        "estimated_weight_kg": 100,
        "scheduled_date": "2026-09-10",
        "scheduled_slot": "10:00-12:00",
        "location_index": 0,
        "notes": "Optional note"
    }

    The institution location is taken from:

        institutions.locations[location_index]

    The institution_id is always taken from the authenticated
    backend user and can NOT be supplied by the client.
    """

    # -----------------------------------------------------
    # Required fields
    # -----------------------------------------------------

    waste_category = str(
        payload.get("waste_category") or ""
    ).strip()

    scheduled_date = str(
        payload.get("scheduled_date") or ""
    ).strip()

    scheduled_slot = str(
        payload.get("scheduled_slot") or ""
    ).strip()

    if not waste_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="waste_category is required",
        )

    if not scheduled_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scheduled_date is required",
        )

    if not scheduled_slot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scheduled_slot is required",
        )

    # -----------------------------------------------------
    # Weight validation
    # -----------------------------------------------------

    try:
        estimated_weight_kg = float(
            payload.get("estimated_weight_kg")
        )
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="estimated_weight_kg must be a valid number",
        )

    if estimated_weight_kg <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="estimated_weight_kg must be greater than 0",
        )

    # -----------------------------------------------------
    # Location index
    # -----------------------------------------------------

    try:
        location_index = int(
            payload.get("location_index")
        )
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="location_index must be a valid integer",
        )

    if location_index < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="location_index must be 0 or greater",
        )

    # -----------------------------------------------------
    # Validate institution locations
    # -----------------------------------------------------

    locations = current_user.get("locations") or []

    if not locations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No institution locations found. "
                "Add a location before scheduling a pickup."
            ),
        )

    if location_index >= len(locations):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected institution location does not exist",
        )

    location = locations[location_index]

    if not isinstance(location, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institution location data is invalid",
        )

    # -----------------------------------------------------
    # DUPLICATE CHECK
    # -----------------------------------------------------
    #
    # Prevent duplicate ACTIVE requests for:
    # institution + location + category + date + slot
    #
    # Cancelled/completed pickups are excluded so a new request
    # can be scheduled later for the same slot.

    duplicate_query = {
        "institution_id": current_user["_id"],
        "location_index": location_index,
        "waste_category": waste_category,
        "scheduled_date": scheduled_date,
        "scheduled_slot": scheduled_slot,
        "status": {
            "$in": [
                "pending",
                "assigned",
                "in_progress",
                "disputed",
            ]
        },
    }

    existing_pickup = await db["pickups"].find_one(
        duplicate_query
    )

    if existing_pickup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A pickup is already scheduled for this "
                "location, waste category, date, and time slot."
            ),
        )

    # -----------------------------------------------------
    # Optional notes
    # -----------------------------------------------------

    notes = payload.get("notes")

    if notes is not None:
        notes = str(notes).strip() or None

    # -----------------------------------------------------
    # Create institution pickup
    # -----------------------------------------------------

    created = await pickup_service.create_institution_pickup(
        db=db,
        institution_id=current_user["_id"],
        location_index=location_index,
        location=location,
        waste_category=waste_category,
        estimated_weight_kg=estimated_weight_kg,
        scheduled_date=scheduled_date,
        scheduled_slot=scheduled_slot,
        notes=notes,
    )

    return serialize_doc(created)


# =========================================================
# LIST MY PICKUPS
# =========================================================

@router.get("/mine")
async def my_pickups(
    status_filter: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    User:
        pickups belonging to user

    Partner:
        pickups assigned to partner

    Institution:
        institution pickups

    Admin:
        all pickups
    """

    repo = PickupRepository(db)

    role = current_user.get("role")

    if role == "partner":

        items = await repo.list_for_partner(
            current_user["_id"],
            status_filter,
        )

    elif role == "institution":

        query = {
            "institution_id": current_user["_id"]
        }

        if status_filter:
            query["status"] = status_filter

        cursor = (
            db["pickups"]
            .find(query)
            .sort("created_at", -1)
        )

        items = [
            doc
            async for doc in cursor
        ]

    elif role == "admin":

        items = await repo.list_all(
            status_filter
        )

    else:

        items = await repo.list_for_user(
            current_user["_id"],
            status_filter,
        )

    return [
        serialize_doc(item)
        for item in items
    ]


# =========================================================
# GET SINGLE PICKUP
# =========================================================

@router.get("/{pickup_id}")
async def get_pickup(
    pickup_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    repo = PickupRepository(db)

    pickup = await repo.get_by_id(
        pickup_id
    )

    if not pickup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pickup not found",
        )

    is_owner = (
        pickup.get("user_id")
        == current_user["_id"]
    )

    is_assigned_partner = (
        pickup.get("partner_id")
        == current_user["_id"]
    )

    is_institution_owner = (
        pickup.get("institution_id")
        == current_user["_id"]
    )

    is_privileged = (
        current_user.get("role")
        == "admin"
    )

    if not (
        is_owner
        or is_assigned_partner
        or is_institution_owner
        or is_privileged
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this pickup",
        )

    return serialize_doc(pickup)


# =========================================================
# ADMIN — ASSIGN PARTNER
# =========================================================

@router.post("/{pickup_id}/assign")
async def assign_pickup(
    pickup_id: str,
    payload: PickupAssign,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign partners",
        )

    await pickup_service.assign_partner(
        db,
        pickup_id,
        payload.partner_id,
        current_user["_id"],
    )

    return {
        "message": "Partner assigned"
    }


# =========================================================
# ADMIN / ASSIGNED PARTNER — UPDATE STATUS
# =========================================================

@router.patch("/{pickup_id}/status")
async def update_pickup_status(
    pickup_id: str,
    payload: PickupStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    repo = PickupRepository(db)

    pickup = await repo.get_by_id(
        pickup_id
    )

    if not pickup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pickup not found",
        )

    role = current_user.get("role")

    is_assigned_partner = (
        pickup.get("partner_id")
        == current_user["_id"]
    )

    if role == "admin":
        authorized = True

    elif (
        role == "partner"
        and is_assigned_partner
    ):
        authorized = True

    else:
        authorized = False

    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this pickup",
        )

    updated = await pickup_service.update_status(
        db,
        pickup_id,
        payload.status,
        current_user["_id"],
        actual_weight_kg=payload.actual_weight_kg,
        notes=payload.notes,
    )

    return serialize_doc(updated)


# =========================================================
# USER — CANCEL PICKUP
# =========================================================

@router.post("/{pickup_id}/cancel")
async def cancel_pickup(
    pickup_id: str,
    current_user: dict = Depends(require_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    repo = PickupRepository(db)

    pickup = await repo.get_by_id(
        pickup_id
    )

    if (
        not pickup
        or pickup.get("user_id")
        != current_user["_id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pickup not found",
        )

    if pickup.get("status") in (
        "completed",
        "cancelled",
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot cancel a "
                f"{pickup['status']} pickup"
            ),
        )

    updated = await pickup_service.update_status(
        db,
        pickup_id,
        "cancelled",
        current_user["_id"],
    )

    return serialize_doc(updated)