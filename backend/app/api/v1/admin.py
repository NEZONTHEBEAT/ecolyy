"""
/api/v1/admin — everything the admin dashboard needs.

Guarded end-to-end by require_admin.

Document workflow:
    Partner uploads
        ↓partner-documents
    Pending Review
        ↓
    Admin Approve → Verified

If partner submits a replacement request:
    Partner → Replacement Requested
        ↓
    Admin Approve Replace → old document removed
        ↓
    Partner can upload again

Admin can also reject/delete a document directly.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.permissions import require_admin
from app.core.security import hash_password
from app.models.audit_log import AuditLogModel
from app.models.user import UserModel
from app.repositories.partner_repository import PartnerRepository
from app.repositories.pickup_repository import PickupRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import (
    AdminStats,
    UserStatusUpdate,
    WasteCategoryCreate,
)
from app.schemas.reward import RewardCreate
from app.services import partner_service
from app.utils.helpers import (
    serialize_doc,
    to_object_id,
    utcnow,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)


# =========================================================
# AUDIT LOG HELPER
# =========================================================

async def _log_action(
    db,
    actor_id: str,
    action: str,
    collection: str,
    target_id: str,
    meta: dict | None = None,
):
    await db["audit_logs"].insert_one(
        AuditLogModel.new(
            actor_id,
            "admin",
            action,
            collection,
            target_id,
            meta,
        )
    )


# =========================================================
# DASHBOARD
# =========================================================

@router.get("/stats", response_model=AdminStats)
async def get_stats(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user_repo = UserRepository(db)
    pickup_repo = PickupRepository(db)

    total_users = await user_repo.count_all()
    total_partners = await db["partners"].count_documents({})
    total_institutions = await db["institutions"].count_documents({})
    total_pickups = await pickup_repo.count_all()
    by_status = await pickup_repo.count_by_status()

    points_pipeline = [
        {
            "$group": {
                "_id": None,
                "total": {
                    "$sum": "$points_awarded"
                },
            }
        }
    ]

    points_result = [
        row
        async for row in db["pickups"].aggregate(
            points_pipeline
        )
    ]

    total_points = (
        points_result[0]["total"]
        if points_result
        else 0
    )

    wallet_pipeline = [
        {
            "$group": {
                "_id": None,
                "total": {
                    "$sum": "$wallet_amount_awarded"
                },
            }
        }
    ]

    wallet_result = [
        row
        async for row in db["pickups"].aggregate(
            wallet_pipeline
        )
    ]

    total_wallet = (
        wallet_result[0]["total"]
        if wallet_result
        else 0.0
    )

    return AdminStats(
        total_users=total_users,
        total_partners=total_partners,
        total_institutions=total_institutions,
        total_pickups=total_pickups,
        pickups_by_status=by_status,
        total_points_awarded=total_points,
        total_wallet_paid_out=total_wallet,
    )


# =========================================================
# USERS
# =========================================================

@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    List users for admin dashboard.

    Password hashes are never returned.
    """

    repo = UserRepository(db)

    items = await repo.list_all(
        skip,
        limit,
        search,
    )

    result = []

    for item in items:
        safe_item = serialize_doc(item)

        # Never expose password hash.
        safe_item.pop(
            "password_hash",
            None,
        )

        result.append(safe_item)

    return result


# =========================================================
# USER — CREATE
# =========================================================

@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: dict,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Create a normal user.

    Admin cannot create another admin using this endpoint.
    Role is always forced to 'user'.
    """

    name = str(
        payload.get(
            "name",
            "",
        )
    ).strip()

    email = str(
        payload.get(
            "email",
            "",
        )
    ).strip().lower()

    phone = payload.get("phone")

    password = str(
        payload.get(
            "password",
            "",
        )
    )

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name is required.",
        )

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required.",
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password is required.",
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters.",
        )

    # -----------------------------------------------------
    # Duplicate email check
    # -----------------------------------------------------

    existing_user = await db["users"].find_one(
        {
            "email": email
        }
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists.",
        )

    # -----------------------------------------------------
    # Password hashing
    # -----------------------------------------------------

    hashed_password = hash_password(
        password
    )

    # -----------------------------------------------------
    # Create user model
    # -----------------------------------------------------

    doc = UserModel.new(
        name=name,
        email=email,
        phone=phone,
        password_hash=hashed_password,
        role="user",
    )

    # -----------------------------------------------------
    # Initial active state
    # -----------------------------------------------------

    if "is_active" in payload:
        doc["is_active"] = bool(
            payload["is_active"]
        )

    # -----------------------------------------------------
    # Insert
    # -----------------------------------------------------

    result = await db["users"].insert_one(doc)

    doc["_id"] = result.inserted_id

    # -----------------------------------------------------
    # Audit log
    # -----------------------------------------------------

    await _log_action(
        db,
        current_user["_id"],
        "create_user",
        "users",
        str(doc["_id"]),
        {
            "email": email,
            "name": name,
        },
    )

    # -----------------------------------------------------
    # Safe response
    # -----------------------------------------------------

    safe_doc = serialize_doc(doc)

    safe_doc.pop(
        "password_hash",
        None,
    )

    return safe_doc


# =========================================================
# USER — GET ONE
# =========================================================

@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get a single user.
    """

    try:
        user_oid = to_object_id(
            user_id
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID.",
        )

    user = await db["users"].find_one(
        {
            "_id": user_oid
        }
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    safe_user = serialize_doc(user)

    safe_user.pop(
        "password_hash",
        None,
    )

    return safe_user


# =========================================================
# USER — UPDATE
# =========================================================

@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: dict,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Update user information.

    Supported fields:

        name
        email
        phone
        password
        is_active

    Role cannot be changed.
    """

    try:
        user_oid = to_object_id(
            user_id
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID.",
        )

    existing_user = await db["users"].find_one(
        {
            "_id": user_oid
        }
    )

    if not existing_user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    # -----------------------------------------------------
    # Never allow admin role modification
    # -----------------------------------------------------

    if existing_user.get("role") == "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin accounts cannot be modified through this endpoint.",
        )

    updates = {}

    # -----------------------------------------------------
    # NAME
    # -----------------------------------------------------

    if "name" in payload:

        name = str(
            payload["name"]
        ).strip()

        if not name:
            raise HTTPException(
                status_code=400,
                detail="Name cannot be empty.",
            )

        updates["name"] = name

    # -----------------------------------------------------
    # EMAIL
    # -----------------------------------------------------

    if "email" in payload:

        email = str(
            payload["email"]
        ).strip().lower()

        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email cannot be empty.",
            )

        duplicate = await db["users"].find_one(
            {
                "email": email,
                "_id": {
                    "$ne": user_oid
                },
            }
        )

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="A user with this email already exists.",
            )

        updates["email"] = email

    # -----------------------------------------------------
    # PHONE
    # -----------------------------------------------------

    if "phone" in payload:
        updates["phone"] = payload["phone"]

    # -----------------------------------------------------
    # PASSWORD
    # -----------------------------------------------------

    if "password" in payload:

        password = str(
            payload["password"]
        )

        if not password:
            raise HTTPException(
                status_code=400,
                detail="Password cannot be empty.",
            )

        if len(password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters.",
            )

        updates["password_hash"] = hash_password(
            password
        )

    # -----------------------------------------------------
    # ACTIVE STATUS
    # -----------------------------------------------------

    if "is_active" in payload:
        updates["is_active"] = bool(
            payload["is_active"]
        )

    # -----------------------------------------------------
    # Role remains unchanged
    # -----------------------------------------------------

    updates["role"] = existing_user.get(
        "role",
        "user",
    )

    updates["updated_at"] = utcnow()

    # -----------------------------------------------------
    # MongoDB update
    # -----------------------------------------------------

    await db["users"].update_one(
        {
            "_id": user_oid
        },
        {
            "$set": updates
        },
    )

    # -----------------------------------------------------
    # Fetch updated user
    # -----------------------------------------------------

    updated_user = await db["users"].find_one(
        {
            "_id": user_oid
        }
    )

    # -----------------------------------------------------
    # Audit log
    # -----------------------------------------------------

    updated_fields = [
        key
        for key in updates.keys()
        if key != "password_hash"
    ]

    await _log_action(
        db,
        current_user["_id"],
        "update_user",
        "users",
        user_id,
        {
            "updated_fields": updated_fields,
        },
    )

    # -----------------------------------------------------
    # Safe response
    # -----------------------------------------------------

    safe_user = serialize_doc(
        updated_user
    )

    safe_user.pop(
        "password_hash",
        None,
    )

    return safe_user


# =========================================================
# USER — DELETE
# =========================================================

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Permanently delete a user.
    """

    try:
        user_oid = to_object_id(
            user_id
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID.",
        )

    existing_user = await db["users"].find_one(
        {
            "_id": user_oid
        }
    )

    if not existing_user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    # -----------------------------------------------------
    # Safety protection
    # -----------------------------------------------------

    if existing_user.get("role") == "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin accounts cannot be deleted from this endpoint.",
        )

    result = await db["users"].delete_one(
        {
            "_id": user_oid
        }
    )

    if result.deleted_count != 1:
        raise HTTPException(
            status_code=404,
            detail="User could not be deleted.",
        )

    # -----------------------------------------------------
    # Audit log
    # -----------------------------------------------------

    await _log_action(
        db,
        current_user["_id"],
        "delete_user",
        "users",
        user_id,
        {
            "email": existing_user.get(
                "email"
            ),
            "name": existing_user.get(
                "name"
            ),
        },
    )

    return {
        "success": True,
        "message": "User deleted successfully.",
        "user_id": user_id,
    }


# =========================================================
# USER — STATUS
# =========================================================

@router.patch("/users/{user_id}/status")
async def set_user_status(
    user_id: str,
    payload: UserStatusUpdate,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Activate or deactivate a user.
    """

    repo = UserRepository(db)

    try:
        user_oid = to_object_id(
            user_id
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID.",
        )

    existing_user = await db["users"].find_one(
        {
            "_id": user_oid
        }
    )

    if not existing_user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    # -----------------------------------------------------
    # Protect admin accounts
    # -----------------------------------------------------

    if existing_user.get("role") == "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin account status cannot be changed here.",
        )

    await repo.set_active(
        user_id,
        payload.is_active,
    )

    await _log_action(
        db,
        current_user["_id"],
        "set_user_status",
        "users",
        user_id,
        {
            "is_active": payload.is_active,
            "reason": payload.reason,
        },
    )

    return {
        "success": True,
        "message": "User status updated successfully.",
        "user_id": user_id,
        "is_active": payload.is_active,
    }


# =========================================================
# PARTNERS
# =========================================================

@router.get("/partners")
async def list_partners(
    skip: int = 0,
    limit: int = 50,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    repo = PartnerRepository(db)

    items = await repo.list_all(
        skip,
        limit,
    )

    return [
        serialize_doc(item)
        for item in items
    ]


@router.patch("/partners/{partner_id}/verify")
async def verify_partner(
    partner_id: str,
    verified: bool = True,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    await partner_service.set_verification(
        db,
        partner_id,
        verified,
    )

    await _log_action(
        db,
        current_user["_id"],
        "verify_partner",
        "partners",
        partner_id,
        {
            "verified": verified
        },
    )

    return {
        "message": "Updated"
    }


# =========================================================
# INSTITUTIONS
# =========================================================

@router.get("/institutions")
async def list_institutions(
    skip: int = 0,
    limit: int = 50,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    cursor = (
        db["institutions"]
        .find({})
        .skip(skip)
        .limit(limit)
        .sort("created_at", -1)
    )

    return [
        serialize_doc(doc)
        async for doc in cursor
    ]


# =========================================================
# PICKUPS
# =========================================================

@router.get("/pickups")
async def list_all_pickups(
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    repo = PickupRepository(db)

    items = await repo.list_all(
        status_filter,
        skip,
        limit,
    )

    return [
        serialize_doc(item)
        for item in items
    ]


@router.get("/pickups/unassigned")
async def list_unassigned_pickups(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    repo = PickupRepository(db)

    items = await repo.list_unassigned()

    return [
        serialize_doc(item)
        for item in items
    ]


# =========================================================
# WASTE CATEGORIES
# =========================================================

@router.get("/waste-categories")
async def list_waste_categories(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    cursor = db["waste_categories"].find({})

    return [
        serialize_doc(doc)
        async for doc in cursor
    ]


@router.post("/waste-categories")
async def create_waste_category(
    payload: WasteCategoryCreate,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    doc = payload.model_dump()

    result = await db[
        "waste_categories"
    ].insert_one(doc)

    doc["_id"] = result.inserted_id

    await _log_action(
        db,
        current_user["_id"],
        "create_waste_category",
        "waste_categories",
        str(doc["_id"]),
    )

    return serialize_doc(doc)


# =========================================================
# REWARDS
# =========================================================

@router.post("/rewards")
async def create_reward(
    payload: RewardCreate,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    from app.models.reward import RewardModel

    doc = RewardModel.new(
        **payload.model_dump()
    )

    result = await db[
        "rewards"
    ].insert_one(doc)

    doc["_id"] = result.inserted_id

    await _log_action(
        db,
        current_user["_id"],
        "create_reward",
        "rewards",
        str(doc["_id"]),
    )

    return serialize_doc(doc)


# =========================================================
# DISPUTES
# =========================================================

@router.get("/disputes")
async def list_disputes(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    cursor = (
        db["pickups"]
        .find({
            "status": "disputed"
        })
        .sort("updated_at", -1)
    )

    return [
        serialize_doc(doc)
        async for doc in cursor
    ]


# =========================================================
# DOCUMENT HELPERS
# =========================================================

def _get_backend_root() -> Path:
    """
    backend/
        uploads/
            partners/
    """
    return Path(__file__).resolve().parents[3]


def _delete_document_file(
    relative_path: str | None,
):
    """
    Safely delete uploaded document file.
    """

    if not relative_path:
        return

    backend_root = _get_backend_root()

    file_path = (
        backend_root
        / relative_path
    ).resolve()

    uploads_root = (
        backend_root
        / "uploads"
        / "partners"
    ).resolve()

    if not str(file_path).startswith(
        str(uploads_root)
    ):
        return

    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass


# =========================================================
# DOCUMENTS — LIST
# =========================================================

@router.get("/partner-documents")
async def list_partner_documents(
    partner_id: str | None = None,
    status_filter: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Return partner documents in a flattened admin-friendly format.
    """

    query = {}

    if partner_id:
        try:
            query["_id"] = to_object_id(
                partner_id
            )
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid partner ID.",
            )

    cursor = (
        db["partners"]
        .find(query)
        .sort("updated_at", -1)
    )

    result = []

    async for partner in cursor:

        documents = partner.get(
            "documents",
            [],
        )

        for document in documents:

            document_status = document.get(
                "status",
                "pending",
            )

            if (
                status_filter
                and document_status != status_filter
            ):
                continue

            result.append(
                {
                    "partner_id": str(
                        partner["_id"]
                    ),
                    "partner_name": partner.get(
                        "name",
                        "",
                    ),
                    "partner_email": partner.get(
                        "email",
                        "",
                    ),
                    "document": serialize_doc(
                        document
                    ),
                }
            )

    return result


# =========================================================
# DOCUMENTS — ADMIN VIEW FILE
# =========================================================

@router.get(
    "/partners/{partner_id}/documents/{document_id}/file"
)
async def view_partner_document_as_admin(
    partner_id: str,
    document_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    try:
        partner_oid = to_object_id(
            partner_id
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid partner ID.",
        )

    partner = await db["partners"].find_one(
        {
            "_id": partner_oid
        }
    )

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Partner not found.",
        )

    documents = partner.get(
        "documents",
        []
    )

    document = next(
        (
            item
            for item in documents
            if item.get("id") == document_id
        ),
        None,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    relative_path = document.get(
        "file_path"
    )

    if not relative_path:
        raise HTTPException(
            status_code=404,
            detail="Document file is unavailable.",
        )

    # ---------------------------------------------------------
    # Backend root
    # ---------------------------------------------------------

    backend_root = (
        Path(__file__).resolve().parents[3]
    )

    file_path = (
        backend_root / relative_path
    ).resolve()

    uploads_root = (
        backend_root
        / "uploads"
        / "partners"
    ).resolve()

    # ---------------------------------------------------------
    # Security: prevent path traversal
    # ---------------------------------------------------------

    try:
        file_path.relative_to(
            uploads_root
        )

    except ValueError:

        raise HTTPException(
            status_code=403,
            detail="Invalid document path.",
        )

    # ---------------------------------------------------------
    # File exists?
    # ---------------------------------------------------------

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Document file does not exist.",
        )

    # ---------------------------------------------------------
    # Return file
    # ---------------------------------------------------------

    return FileResponse(
        path=str(file_path),
        media_type=document.get(
            "content_type",
            "application/octet-stream",
        ),
        filename=document.get(
            "original_filename",
            "document",
        ),
    )


# =========================================================
# DOCUMENTS — APPROVE
# =========================================================

@router.patch(
    "/partners/{partner_id}/documents/{document_id}/approve"
)
async def approve_partner_document(
    partner_id: str,
    document_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    try:
        partner_oid = to_object_id(
            partner_id
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid partner ID.",
        )

    partner = await db[
        "partners"
    ].find_one({
        "_id": partner_oid
    })

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Partner not found.",
        )

    documents = list(
        partner.get(
            "documents",
            [],
        )
    )

    target_document = None

    for document in documents:

        if (
            document.get("id")
            == document_id
        ):
            target_document = document
            break

    if not target_document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    target_document["verified"] = True
    target_document["status"] = "verified"
    target_document["statusLabel"] = "Verified"
    target_document["replacement_requested"] = False
    target_document["updated_at"] = utcnow()

    await db["partners"].update_one(
        {
            "_id": partner_oid
        },
        {
            "$set": {
                "documents": documents,
                "updated_at": utcnow(),
            }
        },
    )

    await _log_action(
        db,
        current_user["_id"],
        "approve_partner_document",
        "partners",
        partner_id,
        {
            "document_id": document_id,
            "document_type": target_document.get(
                "type"
            ),
        },
    )

    return {
        "success": True,
        "message": "Document approved successfully.",
        "document": serialize_doc(
            target_document
        ),
    }


# =========================================================
# DOCUMENTS — REJECT / DELETE
# =========================================================

@router.delete(
    "/partners/{partner_id}/documents/{document_id}"
)
async def reject_delete_partner_document(
    partner_id: str,
    document_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    try:
        partner_oid = to_object_id(
            partner_id
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid partner ID.",
        )

    partner = await db[
        "partners"
    ].find_one({
        "_id": partner_oid
    })

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Partner not found.",
        )

    documents = list(
        partner.get(
            "documents",
            [],
        )
    )

    target_document = next(
        (
            document
            for document in documents
            if document.get("id")
            == document_id
        ),
        None,
    )

    if not target_document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    # Remove physical file
    _delete_document_file(
        target_document.get(
            "file_path"
        )
    )

    remaining_documents = [
        document
        for document in documents
        if document.get("id")
        != document_id
    ]

    await db["partners"].update_one(
        {
            "_id": partner_oid
        },
        {
            "$set": {
                "documents": remaining_documents,
                "updated_at": utcnow(),
            }
        },
    )

    await _log_action(
        db,
        current_user["_id"],
        "reject_delete_partner_document",
        "partners",
        partner_id,
        {
            "document_id": document_id,
            "document_type": target_document.get(
                "type"
            ),
        },
    )

    return {
        "success": True,
        "message": (
            "Document rejected and deleted. "
            "Partner can upload again."
        ),
    }


# =========================================================
# DOCUMENTS — APPROVE REPLACEMENT REQUEST
# =========================================================

@router.patch(
    "/partners/{partner_id}/documents/{document_id}/replace/approve"
)
async def approve_document_replacement(
    partner_id: str,
    document_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    try:
        partner_oid = to_object_id(
            partner_id
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid partner ID.",
        )

    partner = await db[
        "partners"
    ].find_one({
        "_id": partner_oid
    })

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Partner not found.",
        )

    documents = list(
        partner.get(
            "documents",
            [],
        )
    )

    target_document = next(
        (
            document
            for document in documents
            if document.get("id")
            == document_id
        ),
        None,
    )

    if not target_document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    if not target_document.get(
        "replacement_requested",
        False,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "No replacement request exists "
                "for this document."
            ),
        )

    # Delete old physical file
    _delete_document_file(
        target_document.get(
            "file_path"
        )
    )

    # Remove old document completely.
    # Partner will see Upload again.
    remaining_documents = [
        document
        for document in documents
        if document.get("id")
        != document_id
    ]

    await db["partners"].update_one(
        {
            "_id": partner_oid
        },
        {
            "$set": {
                "documents": remaining_documents,
                "updated_at": utcnow(),
            }
        },
    )

    await _log_action(
        db,
        current_user["_id"],
        "approve_document_replacement",
        "partners",
        partner_id,
        {
            "document_id": document_id,
            "document_type": target_document.get(
                "type"
            ),
        },
    )

    return {
        "success": True,
        "message": (
            "Replacement request approved. "
            "Old document removed. "
            "Partner can upload a new document."
        ),
    }


# =========================================================
# DOCUMENTS — REJECT REPLACEMENT REQUEST
# =========================================================

@router.patch(
    "/partners/{partner_id}/documents/{document_id}/replace/reject"
)
async def reject_document_replacement(
    partner_id: str,
    document_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    try:
        partner_oid = to_object_id(
            partner_id
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid partner ID.",
        )

    partner = await db[
        "partners"
    ].find_one({
        "_id": partner_oid
    })

    if not partner:
        raise HTTPException(
            status_code=404,
            detail="Partner not found.",
        )

    documents = list(
        partner.get(
            "documents",
            [],
        )
    )

    target_document = next(
        (
            document
            for document in documents
            if document.get("id")
            == document_id
        ),
        None,
    )

    if not target_document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    if not target_document.get(
        "replacement_requested",
        False,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "No replacement request exists "
                "for this document."
            ),
        )

    target_document[
        "replacement_requested"
    ] = False

    target_document[
        "replacement_status"
    ] = "rejected"

    target_document[
        "updated_at"
    ] = utcnow()

    await db["partners"].update_one(
        {
            "_id": partner_oid
        },
        {
            "$set": {
                "documents": documents,
                "updated_at": utcnow(),
            }
        },
    )

    await _log_action(
        db,
        current_user["_id"],
        "reject_document_replacement",
        "partners",
        partner_id,
        {
            "document_id": document_id,
            "document_type": target_document.get(
                "type"
            ),
        },
    )

    return {
        "success": True,
        "message": (
            "Replacement request rejected. "
            "Existing document remains valid."
        ),
    }


# =========================================================
# AUDIT LOG
# =========================================================

@router.get("/audit-logs")
async def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    cursor = (
        db["audit_logs"]
        .find({})
        .skip(skip)
        .limit(limit)
        .sort("created_at", -1)
    )

    return [
        serialize_doc(doc)
        async for doc in cursor
    ]