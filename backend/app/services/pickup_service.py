"""
Pickup lifecycle:

USER:
    create -> assign -> in_progress -> completed

INSTITUTION:
    schedule -> assign -> in_progress -> completed

On completion:
- points are calculated
- wallet payout is calculated
- user wallet is credited
- partner statistics are updated
- partner earning is stored on the pickup
- notifications are sent
"""

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.pickup import PickupModel
from app.repositories.partner_repository import PartnerRepository
from app.repositories.pickup_repository import PickupRepository
from app.repositories.user_repository import UserRepository
from app.services import wallet_service
from app.services.notification_service import notify
from app.utils.helpers import utcnow


DEFAULT_POINTS_PER_KG = 10
DEFAULT_WALLET_RATE_PER_KG = 5.0


# =========================================================
# USER PICKUP
# =========================================================

async def create_pickup(
    db: AsyncIOMotorDatabase,
    user_id: str,
    payload,
) -> dict:

    address = await db["addresses"].find_one(
        {
            "_id": __import__("bson").ObjectId(
                payload.address_id
            ),
            "user_id": user_id,
        }
    )

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    address_snapshot = {
        "label": address["label"],
        "line1": address["line1"],
        "line2": address.get("line2"),
        "city": address["city"],
        "state": address["state"],
        "pincode": address["pincode"],
    }

    doc = PickupModel.new(
        user_id=user_id,
        waste_category=payload.waste_category,
        estimated_weight_kg=payload.estimated_weight_kg,
        address_id=payload.address_id,
        address_snapshot=address_snapshot,
        scheduled_date=payload.scheduled_date,
        scheduled_slot=payload.scheduled_slot,
        institution_id=payload.institution_id,
    )

    if payload.notes:
        doc["notes"] = payload.notes

    repo = PickupRepository(db)

    created = await repo.create(doc)

    await notify(
        db,
        user_id=user_id,
        role="user",
        title="Pickup scheduled",
        message=(
            f"Your {payload.waste_category} "
            f"pickup is booked for "
            f"{payload.scheduled_date}."
        ),
    )

    return created


# =========================================================
# INSTITUTION PICKUP
# =========================================================

async def create_institution_pickup(
    db: AsyncIOMotorDatabase,
    institution_id: str,
    location_index: int,
    location: dict,
    waste_category: str,
    estimated_weight_kg: float,
    scheduled_date: str,
    scheduled_slot: str,
    notes: str | None = None,
) -> dict:
    """
    Create a pickup for an institution.

    Institution locations are embedded inside the
    institution document, so there is no users.addresses
    lookup here.

    The generated pickup contains:
        institution_id
        address_id
        address_snapshot
        waste_category
        estimated_weight_kg
        scheduled_date
        scheduled_slot
        status
        timeline
    """

    # -----------------------------------------------------
    # Validate location
    # -----------------------------------------------------

    if not isinstance(location, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid institution location",
        )

    label = str(
        location.get("label")
        or f"Institution Location {location_index + 1}"
    ).strip()

    address = str(
        location.get("address") or ""
    ).strip()

    if not address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institution location address is required",
        )

    # -----------------------------------------------------
    # Address identifier
    # -----------------------------------------------------

    address_id = (
        f"institution-location-{location_index}"
    )

    address_snapshot = {
        "label": label,
        "address": address,
        "lat": location.get("lat"),
        "lng": location.get("lng"),
    }

    # -----------------------------------------------------
    # Build pickup document
    # -----------------------------------------------------

    now = utcnow()

    doc = PickupModel.new(
        user_id=None,
        waste_category=waste_category,
        estimated_weight_kg=estimated_weight_kg,
        address_id=address_id,
        address_snapshot=address_snapshot,
        scheduled_date=scheduled_date,
        scheduled_slot=scheduled_slot,
        institution_id=institution_id,
    )

    # -----------------------------------------------------
    # Institution pickups do not belong to a normal user.
    # Preserve the field but store the creator institution.
    # -----------------------------------------------------

    doc["institution_id"] = institution_id
    doc["user_id"] = None
    doc["created_by_role"] = "institution"
    doc["created_by_id"] = institution_id
    doc["location_index"] = location_index

    if notes:
        doc["notes"] = notes

    # Make sure timeline begins with institution actor.
    doc["timeline"] = [
        {
            "status": "pending",
            "at": now,
            "by": institution_id,
        }
    ]

    repo = PickupRepository(db)

    created = await repo.create(doc)

    # -----------------------------------------------------
    # Notification to institution
    # -----------------------------------------------------
    #
    # The notification service already supports user_id,
    # but institution dashboards do not currently have a
    # separate notification API dependency in this flow.
    # We therefore keep creation independent from optional
    # notification failures.
    # -----------------------------------------------------

    try:

        await notify(
            db,
            user_id=institution_id,
            role="institution",
            title="Pickup scheduled",
            message=(
                f"Your {waste_category} pickup "
                f"is scheduled for {scheduled_date}."
            ),
        )

    except Exception:
        # Pickup creation must not fail only because
        # notification delivery failed.
        pass

    return created


# =========================================================
# ASSIGN PARTNER
# =========================================================

async def assign_partner(
    db: AsyncIOMotorDatabase,
    pickup_id: str,
    partner_id: str,
    actor_id: str,
) -> None:

    partner_repo = PartnerRepository(db)

    partner = await partner_repo.get_by_id(
        partner_id
    )

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner not found",
        )

    repo = PickupRepository(db)

    pickup = await repo.get_by_id(
        pickup_id
    )

    if not pickup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pickup not found",
        )

    await repo.assign_partner(
        pickup_id,
        partner_id,
        actor_id,
    )

    # -----------------------------------------------------
    # Partner notification
    # -----------------------------------------------------

    await notify(
        db,
        user_id=partner_id,
        role="partner",
        title="New pickup assigned",
        message=(
            f"You've been assigned a "
            f"{pickup['waste_category']} pickup "
            f"on {pickup['scheduled_date']}."
        ),
    )

    # -----------------------------------------------------
    # User notification
    #
    # Only normal-user pickups have user_id.
    # Institution pickups have user_id=None.
    # -----------------------------------------------------

    user_id = pickup.get("user_id")

    if user_id:

        await notify(
            db,
            user_id=user_id,
            role="user",
            title="Partner assigned",
            message=(
                "A recycling partner has been assigned "
                "to your pickup."
            ),
        )

    # -----------------------------------------------------
    # Institution notification
    # -----------------------------------------------------

    institution_id = pickup.get(
        "institution_id"
    )

    if institution_id:

        try:

            await notify(
                db,
                user_id=institution_id,
                role="institution",
                title="Partner assigned",
                message=(
                    "A recycling partner has been "
                    "assigned to your pickup."
                ),
            )

        except Exception:
            pass


# =========================================================
# UPDATE STATUS
# =========================================================

async def update_status(
    db: AsyncIOMotorDatabase,
    pickup_id: str,
    new_status: str,
    actor_id: str,
    actual_weight_kg: float | None = None,
    notes: str | None = None,
) -> dict:

    repo = PickupRepository(db)

    pickup = await repo.get_by_id(
        pickup_id
    )

    if not pickup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pickup not found",
        )

    extra: dict = {}

    if notes:
        extra["notes"] = notes

    # =====================================================
    # COMPLETION
    # =====================================================

    if new_status == "completed":

        if actual_weight_kg is None:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "actual_weight_kg is required "
                    "to complete a pickup"
                ),
            )

        if actual_weight_kg <= 0:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "actual_weight_kg must be greater "
                    "than 0"
                ),
            )

        category = await db[
            "waste_categories"
        ].find_one(
            {
                "name":
                    pickup["waste_category"]
            }
        )

        points_rate = (
            category["points_per_kg"]
            if category
            else DEFAULT_POINTS_PER_KG
        )

        wallet_rate = (
            category["wallet_rate_per_kg"]
            if category
            else DEFAULT_WALLET_RATE_PER_KG
        )

        points_awarded = round(
            actual_weight_kg *
            points_rate
        )

        wallet_awarded = round(
            actual_weight_kg *
            wallet_rate,
            2
        )

        extra.update(
            {
                "actual_weight_kg":
                    actual_weight_kg,

                "points_awarded":
                    points_awarded,

                "wallet_amount_awarded":
                    wallet_awarded,
            }
        )

        # -------------------------------------------------
        # Normal user payout
        #
        # Institution pickups have user_id=None, so they
        # do not receive a normal user wallet payout.
        # -------------------------------------------------

        user_id = pickup.get("user_id")

        if user_id:

            user_repo = UserRepository(db)

            await user_repo.increment_points(
                user_id,
                points_awarded,
            )

            await wallet_service.credit_wallet(
                db,
                user_id,
                wallet_awarded,
                "Pickup payout",
                pickup_id,
            )

            await notify(
                db,
                user_id=user_id,
                role="user",
                title="Pickup completed",
                message=(
                    f"You earned "
                    f"{points_awarded} points and "
                    f"₹{wallet_awarded} "
                    f"for this pickup!"
                ),
            )

        # -------------------------------------------------
        # Partner earnings + statistics
        # -------------------------------------------------

        partner_id = pickup.get(
            "partner_id"
        )

        if partner_id:

            partner_earning = round(
                wallet_rate *
                actual_weight_kg *
                0.1,
                2
            )

            # Store the partner earning directly on
            # the completed pickup so the frontend
            # earnings history can display it.
            extra["partner_earning"] = (
                partner_earning
            )

            partner_repo = PartnerRepository(
                db
            )

            await partner_repo.increment_stats(
                partner_id,
                pickups_delta=1,
                earnings_delta=partner_earning,
            )

            # Optional partner notification.
            try:

                await notify(
                    db,
                    user_id=partner_id,
                    role="partner",
                    title="Pickup completed",
                    message=(
                        f"Pickup completed successfully. "
                        f"You earned ₹{partner_earning}."
                    ),
                )

            except Exception:
                pass

        # -------------------------------------------------
        # Institution notification
        # -------------------------------------------------

        institution_id = pickup.get(
            "institution_id"
        )

        if institution_id:

            try:

                await notify(
                    db,
                    user_id=institution_id,
                    role="institution",
                    title="Pickup completed",
                    message=(
                        f"Your {pickup['waste_category']} "
                        f"pickup has been completed."
                    ),
                )

            except Exception:
                pass

    # =====================================================
    # STATUS UPDATE
    # =====================================================

    await repo.update_status(
        pickup_id,
        new_status,
        actor_id,
        extra,
    )

    updated = await repo.get_by_id(
        pickup_id
    )

    return updated
