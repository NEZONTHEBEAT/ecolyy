"""
/api/v1/partners — partner's own dashboard:
assigned pickups, earnings, documents, profile.

Document workflow:

1. Partner uploads a document
2. Document becomes Pending Review
3. Admin approves -> Verified
4. Partner can request replacement
5. Admin approves replacement request
6. Old document is removed
7. Partner can upload a new document

Partner cannot directly delete or replace an uploaded document.
"""

from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.permissions import require_partner
from app.repositories.pickup_repository import PickupRepository
from app.services import partner_service
from app.utils.helpers import (
    serialize_doc,
    to_object_id,
    utcnow,
)

router = APIRouter(
    prefix="/partners",
    tags=["Partners"],
)


# =========================================================
# PARTNER PROFILE
# =========================================================

@router.get("/me")
async def get_my_partner_profile(
    current_user: dict = Depends(require_partner),
):
    return serialize_doc(current_user)


# =========================================================
# PARTNER PICKUPS
# =========================================================

@router.get("/me/pickups")
async def get_my_assigned_pickups(
    status_filter: str | None = None,
    current_user: dict = Depends(require_partner),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    repo = PickupRepository(db)

    items = await repo.list_for_partner(
        current_user["_id"],
        status_filter,
    )

    return [
        serialize_doc(item)
        for item in items
    ]


@router.get("/me/available-pickups")
async def get_available_pickups(
    current_user: dict = Depends(require_partner),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Unassigned pending pickups a partner could pick up."""

    repo = PickupRepository(db)

    items = await repo.list_unassigned()

    return [
        serialize_doc(item)
        for item in items
    ]


# =========================================================
# PARTNER EARNINGS
# =========================================================

@router.get("/me/earnings")
async def get_my_earnings(
    current_user: dict = Depends(require_partner),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await partner_service.get_earnings_summary(
        db,
        current_user["_id"],
    )


# =========================================================
# PARTNER PROFILE UPDATE
# =========================================================

@router.patch("/me/profile")
async def update_partner_profile(
    payload: dict,
    current_user: dict = Depends(require_partner),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    allowed = {
        "name",
        "phone",
        "vehicle_type",
        "service_areas",
    }

    updates = {
        key: value
        for key, value in payload.items()
        if key in allowed
    }

    if updates:
        updates["updated_at"] = utcnow()

        await db["partners"].update_one(
            {
                "_id": to_object_id(
                    str(current_user["_id"])
                )
            },
            {
                "$set": updates
            },
        )

    updated = await db["partners"].find_one(
        {
            "_id": to_object_id(
                str(current_user["_id"])
            )
        }
    )

    return serialize_doc(updated)


# =========================================================
# DOCUMENT CONFIG
# =========================================================

ALLOWED_DOCUMENT_TYPES = {
    "identity",
    "address",
    "vehicle",
    "bank",
    "insurance",
    "tax",
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# =========================================================
# UPLOAD PATH
# =========================================================

def get_upload_root() -> Path:
    """
    backend/
    └── uploads/
        └── partners/
            └── <partner_id>/
    """

    backend_root = (
        Path(__file__).resolve().parents[3]
    )

    upload_root = (
        backend_root
        / "uploads"
        / "partners"
    )

    upload_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    return upload_root


# =========================================================
# DOCUMENT FILE DELETE HELPER
# =========================================================

def delete_document_file(
    relative_path: str | None,
) -> None:
    """
    Safely delete a document from local storage.
    Only files inside backend/uploads/partners are allowed.
    """

    if not relative_path:
        return

    backend_root = (
        Path(__file__).resolve().parents[3]
    )

    file_path = (
        backend_root
        / relative_path
    ).resolve()

    uploads_root = (
        backend_root
        / "uploads"
        / "partners"
    ).resolve()

    try:
        file_path.relative_to(
            uploads_root
        )
    except ValueError:
        return

    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass


# =========================================================
# GET MY DOCUMENTS
# =========================================================

@router.get("/me/documents")
async def get_my_documents(
    current_user: dict = Depends(require_partner),
):
    documents = current_user.get(
        "documents",
        [],
    )

    return documents


# =========================================================
# UPLOAD DOCUMENT
# =========================================================

@router.post("/me/documents")
async def upload_partner_document(
    document_type: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_partner),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    document_type = (
        document_type.strip().lower()
    )

    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid document type. "
                "Allowed: identity, address, vehicle, "
                "bank, insurance, tax."
            ),
        )

    # ---------------------------------------------------------
    # Existing document check
    # ---------------------------------------------------------

    existing_documents = list(
        current_user.get(
            "documents",
            [],
        )
    )

    existing_document = next(
        (
            document
            for document in existing_documents
            if document.get("type")
            == document_type
        ),
        None,
    )

    # Partner must NOT directly replace an existing document.
    # The admin has to remove it first by approving a rejection
    # or replacement request.
    if existing_document:
        if existing_document.get(
            "replacement_requested",
            False,
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "A replacement request is already "
                    "pending admin approval."
                ),
            )

        if existing_document.get(
            "verified",
            False,
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "This document is already verified. "
                    "Please request a replacement from admin."
                ),
            )

        raise HTTPException(
            status_code=409,
            detail=(
                "A document of this type already exists "
                "and is under review."
            ),
        )

    # ---------------------------------------------------------
    # Validate file
    # ---------------------------------------------------------

    original_filename = (
        file.filename
        or "document"
    )

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Allowed: PDF, JPG, JPEG, PNG, WEBP."
            ),
        )

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size must be 10 MB or less.",
        )

    # ---------------------------------------------------------
    # Create partner upload directory
    # ---------------------------------------------------------

    partner_id = str(
        current_user["_id"]
    )

    partner_folder = (
        get_upload_root()
        / partner_id
    )

    partner_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Generate safe filename
    # ---------------------------------------------------------

    document_id = uuid4().hex

    safe_filename = (
        f"{document_id}{extension}"
    )

    file_path = (
        partner_folder
        / safe_filename
    )

    file_path.write_bytes(
        file_content
    )

    # ---------------------------------------------------------
    # Relative path
    # ---------------------------------------------------------

    backend_root = (
        Path(__file__).resolve().parents[3]
    )

    relative_file_path = str(
        file_path.relative_to(
            backend_root
        )
    ).replace("\\", "/")

    # ---------------------------------------------------------
    # Document object
    # ---------------------------------------------------------

    now = utcnow()

    document = {
        "id": document_id,
        "type": document_type,
        "original_filename": original_filename,
        "file_path": relative_file_path,
        "url": (
            "/api/v1/partners/me/documents/"
            f"{document_id}/file"
        ),
        "content_type": (
            file.content_type
            or "application/octet-stream"
        ),
        "file_size": len(file_content),
        "verified": False,
        "status": "pending",
        "statusLabel": "Pending Review",
        "replacement_requested": False,
        "replacement_status": None,
        "created_at": now,
        "updated_at": now,
    }

    # ---------------------------------------------------------
    # Save document
    # ---------------------------------------------------------

    updated_documents = [
        *existing_documents,
        document,
    ]

    partner_oid = to_object_id(
        str(current_user["_id"])
    )

    await db["partners"].update_one(
        {
            "_id": partner_oid
        },
        {
            "$set": {
                "documents": updated_documents,
                "updated_at": now,
            }
        },
    )

    return serialize_doc(
        document
    )


# =========================================================
# REQUEST DOCUMENT REPLACEMENT
# =========================================================

@router.patch(
    "/me/documents/{document_id}/replace-request"
)
async def request_document_replacement(
    document_id: str,
    current_user: dict = Depends(require_partner),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Partner can request replacement only for a verified
    document.

    The current document remains active until admin approves
    the replacement request.
    """

    documents = list(
        current_user.get(
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
        "verified",
        False,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only a verified document can "
                "have a replacement request."
            ),
        )

    if target_document.get(
        "replacement_requested",
        False,
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Replacement request is already "
                "pending admin approval."
            ),
        )

    target_document[
        "replacement_requested"
    ] = True

    target_document[
        "replacement_status"
    ] = "pending"

    target_document[
        "statusLabel"
    ] = "Replacement Requested"

    target_document[
        "updated_at"
    ] = utcnow()

    await db["partners"].update_one(
        {
            "_id": to_object_id(
                str(current_user["_id"])
            )
        },
        {
            "$set": {
                "documents": documents,
                "updated_at": utcnow(),
            }
        },
    )

    return {
        "success": True,
        "message": (
            "Replacement request sent to admin."
        ),
        "document": serialize_doc(
            target_document
        ),
    }


# =========================================================
# VIEW / DOWNLOAD DOCUMENT
# =========================================================

@router.get(
    "/me/documents/{document_id}/file"
)
async def view_partner_document(
    document_id: str,
    current_user: dict = Depends(require_partner),
):
    documents = current_user.get(
        "documents",
        [],
    )

    document = next(
        (
            item
            for item in documents
            if item.get("id")
            == document_id
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

    backend_root = (
        Path(__file__).resolve().parents[3]
    )

    file_path = (
        backend_root
        / relative_path
    ).resolve()

    uploads_root = (
        backend_root
        / "uploads"
        / "partners"
    ).resolve()

    try:
        file_path.relative_to(
            uploads_root
        )
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Invalid document path.",
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document file does not exist.",
        )

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
