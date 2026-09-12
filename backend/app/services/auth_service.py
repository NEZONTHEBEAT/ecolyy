"""
Ecolyy Authentication Service

Authentication methods:
- Google Sign-In
- Email OTP
- Password Login

Security rules:
- Frontend never decides the role.
- Backend determines role from verified account email.
- Email and phone numbers must be unique.
- Admin -> Google only
- Partner -> Email + Password only
- Institution -> Email + Password only
- User -> Google / Email OTP
"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

from app.models.user import UserModel
from app.models.partner import PartnerModel
from app.models.institution import InstitutionModel
from app.models.wallet import WalletModel

from app.services.google_auth_service import verify_google_token
from app.utils.helpers import serialize_doc


# =========================================================
# ROLE -> COLLECTION
# =========================================================

ROLE_COLLECTION = {
    "user": "users",
    "admin": "users",
    "partner": "partners",
    "institution": "institutions",
}


# =========================================================
# ROLE DETECTION
# =========================================================

def get_role_from_email(email: str) -> str:
    """
    Backend is the single source of truth for role detection.
    """

    return settings.detect_role_from_email(
        email.strip().lower()
    )


def _get_collection_for_role(role: str) -> str:
    collection = ROLE_COLLECTION.get(role)

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account role",
        )

    return collection


def _ensure_password_login_allowed(role: str) -> None:
    """
    Only partner and institution may use password login.
    """

    if role not in ("partner", "institution"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Password login is available only for "
                "partner and institution accounts."
            ),
        )


def _ensure_google_login_allowed(role: str) -> None:
    """
    Only admin and user may use Google login.
    """

    if role not in ("admin", "user"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Google Sign-In is not available for "
                "partner or institution accounts."
            ),
        )


# =========================================================
# USER INITIALS
# =========================================================

def _build_initials(name: str) -> str:

    name = (name or "User").strip()

    parts = name.split()

    if len(parts) >= 2:
        return (
            parts[0][0] +
            parts[-1][0]
        ).upper()

    if parts:
        return parts[0][0].upper()

    return "U"


# =========================================================
# SAFE RESPONSE + TOKENS
# =========================================================

def _issue_tokens(
    user_id: str,
    role: str,
    user_doc: dict,
) -> dict:

    access_token = create_access_token(
        subject=user_id,
        extra_claims={
            "role": role,
        },
    )

    refresh_token = create_refresh_token(
        subject=user_id,
    )

    safe_user = serialize_doc(user_doc)

    # Never expose sensitive fields
    safe_user.pop("password_hash", None)
    safe_user.pop("google_id", None)

    # Backend-controlled role
    safe_user["role"] = role

    safe_user["initials"] = _build_initials(
        safe_user.get("name", "User")
    )

    safe_user["redirect_url"] = (
        settings.get_redirect_url_for_role(role)
    )

    safe_user["display_role"] = (
        settings.get_display_role(role)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": role,
        "user": safe_user,
    }


# =========================================================
# FIND ACCOUNT BY EMAIL
# =========================================================

async def find_account_by_email(
    db: AsyncIOMotorDatabase,
    email: str,
) -> tuple[dict | None, str | None]:

    email = email.strip().lower()

    for collection_name in (
        "users",
        "partners",
        "institutions",
    ):

        account = await db[collection_name].find_one(
            {
                "email": email,
            }
        )

        if account:
            return account, collection_name

    return None, None


# =========================================================
# FIND ACCOUNT BY PHONE
# =========================================================

async def find_account_by_phone(
    db: AsyncIOMotorDatabase,
    phone: str,
) -> tuple[dict | None, str | None]:

    if not phone:
        return None, None

    phone = phone.strip()

    for collection_name in (
        "users",
        "partners",
        "institutions",
    ):

        account = await db[collection_name].find_one(
            {
                "phone": phone,
            }
        )

        if account:
            return account, collection_name

    return None, None


# =========================================================
# CHECK EMAIL AVAILABILITY
# =========================================================

async def ensure_email_available(
    db: AsyncIOMotorDatabase,
    email: str,
    exclude_user_id=None,
) -> None:

    email = email.strip().lower()

    for collection_name in (
        "users",
        "partners",
        "institutions",
    ):

        account = await db[collection_name].find_one(
            {
                "email": email,
            }
        )

        if not account:
            continue

        if (
            exclude_user_id
            and str(account["_id"]) == str(exclude_user_id)
        ):
            continue

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already used by another account",
        )


# =========================================================
# CHECK PHONE AVAILABILITY
# =========================================================

async def ensure_phone_available(
    db: AsyncIOMotorDatabase,
    phone: str,
    exclude_user_id=None,
) -> None:

    if not phone:
        return

    phone = phone.strip()

    for collection_name in (
        "users",
        "partners",
        "institutions",
    ):

        account = await db[collection_name].find_one(
            {
                "phone": phone,
            }
        )

        if not account:
            continue

        if (
            exclude_user_id
            and str(account["_id"]) == str(exclude_user_id)
        ):
            continue

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This phone number is already used by another account",
        )


# =========================================================
# NORMAL REGISTRATION
# =========================================================

async def register(
    db: AsyncIOMotorDatabase,
    name: str,
    email: str,
    password: str,
    phone: str | None = None,
) -> dict:
    """
    Public registration is ONLY for normal users.

    Admin / Partner / Institution accounts are controlled accounts
    and cannot be created through public registration.
    """

    email = email.strip().lower()

    actual_role = get_role_from_email(email)

    # Special accounts cannot self-register
    if actual_role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "This email belongs to a restricted account. "
                "Public registration is not allowed."
            ),
        )

    await ensure_email_available(
        db,
        email,
    )

    if phone:
        await ensure_phone_available(
            db,
            phone,
        )

    hashed_password = hash_password(password)

    doc = UserModel.new(
        name=name.strip(),
        email=email,
        phone=phone.strip() if phone else None,
        password_hash=hashed_password,
        google_id=None,
        role="user",
    )

    collection = db["users"]

    result = await collection.insert_one(doc)

    doc["_id"] = result.inserted_id

    await db["wallets"].insert_one(
        WalletModel.new(
            str(doc["_id"])
        )
    )

    return _issue_tokens(
        str(doc["_id"]),
        "user",
        doc,
    )


# =========================================================
# PASSWORD LOGIN
# =========================================================

async def login(
    db: AsyncIOMotorDatabase,
    email: str,
    password: str,
) -> dict:
    """
    Password login is allowed only for:
    - partner
    - institution
    """

    email = email.strip().lower()

    actual_role = get_role_from_email(email)

    _ensure_password_login_allowed(actual_role)

    doc, collection_name = await find_account_by_email(
        db,
        email,
    )

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if doc.get("is_active") is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Validate DB collection against backend role
    expected_collection = _get_collection_for_role(
        actual_role
    )

    if expected_collection != collection_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account role configuration is invalid",
        )

    stored_password = doc.get("password_hash")

    if not stored_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password login is not configured for this account",
        )

    try:
        password_valid = verify_password(
            password,
            stored_password,
        )
    except Exception:
        password_valid = False

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return _issue_tokens(
        str(doc["_id"]),
        actual_role,
        doc,
    )


# =========================================================
# GOOGLE LOGIN
# =========================================================

async def google_login(
    db: AsyncIOMotorDatabase,
    id_token_str: str,
) -> dict:
    """
    Google login is allowed only for:
    - admin
    - user

    Partner / institution must use password login.
    """

    payload = verify_google_token(
        id_token_str
    )

    email = payload["email"].strip().lower()

    google_id = payload["google_id"]

    name = (
        payload.get("name")
        or email.split("@")[0]
    ).strip()

    actual_role = get_role_from_email(
        email
    )

    _ensure_google_login_allowed(
        actual_role
    )

    doc, collection_name = await find_account_by_email(
        db,
        email,
    )

    expected_collection = _get_collection_for_role(
        actual_role
    )

    # =====================================================
    # NEW ACCOUNT
    # =====================================================

    if not doc:

        # New Google account can only be user/admin
        doc = UserModel.new(
            name=name,
            email=email,
            phone=None,
            password_hash=None,
            google_id=google_id,
            role=actual_role,
        )

        doc["is_verified"] = True

        collection = db[expected_collection]

        result = await collection.insert_one(doc)

        doc["_id"] = result.inserted_id

        if actual_role == "user":

            await db["wallets"].insert_one(
                WalletModel.new(
                    str(doc["_id"])
                )
            )

    # =====================================================
    # EXISTING ACCOUNT
    # =====================================================

    else:

        if doc.get("is_active") is False:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        if collection_name != expected_collection:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account role configuration is invalid",
            )

        updates = {
            "google_id": google_id,
            "is_verified": True,
            "updated_at": datetime.now(
                timezone.utc
            ),
            "role": actual_role,
        }

        await db[collection_name].update_one(
            {
                "_id": doc["_id"],
            },
            {
                "$set": updates,
            },
        )

        doc.update(updates)

    return _issue_tokens(
        str(doc["_id"]),
        actual_role,
        doc,
    )


# =========================================================
# FIND OR CREATE USER
# Compatibility helper
# =========================================================

async def find_or_create_user(
    db: AsyncIOMotorDatabase,
    email: str,
    name: str,
    password: str | None = None,
    role: str = "user",
) -> dict:
    """
    Compatibility helper.

    Backend role detection always wins over the supplied role.
    """

    email = email.strip().lower()

    doc, _ = await find_account_by_email(
        db,
        email,
    )

    if doc:
        return doc

    actual_role = get_role_from_email(
        email
    )

    hashed_password = None

    if password:
        hashed_password = hash_password(
            password
        )

    # Normal user/admin
    if actual_role in ("user", "admin"):

        doc = UserModel.new(
            name=name.strip(),
            email=email,
            phone=None,
            password_hash=hashed_password,
            google_id=None,
            role=actual_role,
        )

        collection = db["users"]

    # Controlled accounts
    elif actual_role == "partner":

        doc = PartnerModel.new(
            name=name.strip(),
            email=email,
            phone="",
            password_hash=hashed_password,
        )

        doc["role"] = "partner"

        collection = db["partners"]

    elif actual_role == "institution":

        doc = InstitutionModel.new(
            name=name.strip(),
            email=email,
            phone="",
            password_hash=hashed_password,
        )

        doc["role"] = "institution"

        collection = db["institutions"]

    else:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account role",
        )

    result = await collection.insert_one(doc)

    doc["_id"] = result.inserted_id

    if actual_role == "user":

        await db["wallets"].insert_one(
            WalletModel.new(
                str(doc["_id"])
            )
        )

    return doc