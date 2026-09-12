"""
=========================================================
Ecolyy - Authentication & Role-Based Permissions
=========================================================

Roles:
    user
    partner
    institution
    admin

IMPORTANT:
- Never trust role from localStorage.
- Never trust a client-selected role.
- JWT role is NOT the source of truth.
- Backend determines the real role from the verified
  account email stored in MongoDB.
=========================================================
"""

from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.database import get_database
from app.core.security import JWTError, decode_token


# =========================================================
# OAuth2
# =========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


# =========================================================
# Common Authentication Exception
# =========================================================

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={
        "WWW-Authenticate": "Bearer",
    },
)


# =========================================================
# Role -> MongoDB Collection
# =========================================================

ROLE_COLLECTIONS = {
    "user": "users",
    "admin": "users",
    "partner": "partners",
    "institution": "institutions",
}


# =========================================================
# Helper: Find Account By ID
# =========================================================

async def _find_account_by_id(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> tuple[Optional[dict], Optional[str]]:
    """
    Search all supported account collections.

    We intentionally DO NOT use the JWT role to decide
    which collection to search.
    """

    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        return None, None

    # -----------------------------------------------------
    # Users collection
    # -----------------------------------------------------

    user = await db["users"].find_one(
        {"_id": object_id}
    )

    if user is not None:
        return user, "users"

    # -----------------------------------------------------
    # Partners collection
    # -----------------------------------------------------

    partner = await db["partners"].find_one(
        {"_id": object_id}
    )

    if partner is not None:
        return partner, "partners"

    # -----------------------------------------------------
    # Institutions collection
    # -----------------------------------------------------

    institution = await db["institutions"].find_one(
        {"_id": object_id}
    )

    if institution is not None:
        return institution, "institutions"

    return None, None


# =========================================================
# Helper: Resolve Real Role From Email
# =========================================================

def _resolve_role_from_email(email: str) -> str:
    """
    Backend-controlled role detection.

    Special accounts:
        neelspunkryderz71@gmail.com
            -> admin

        shamik.b.1123@inspiria.edu.in
            -> institution

        himanshu.b.11231@gmail.com
            -> partner

    Everything else:
        -> user
    """

    if not email:
        return "user"

    return settings.detect_role_from_email(
        email.strip().lower()
    )


# =========================================================
# Helper: Ensure Collection Matches Role
# =========================================================

def _collection_matches_role(
    collection_name: str,
    role: str,
) -> bool:
    """
    Prevent account data from existing in the wrong
    collection for its email-derived role.
    """

    expected_collection = ROLE_COLLECTIONS.get(role)

    return collection_name == expected_collection


# =========================================================
# GET CURRENT USER
# =========================================================

async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> dict:
    """
    Authenticate the request and return the real current user.

    SECURITY FLOW:

        Authorization Header
                ↓
             JWT Decode
                ↓
          Validate access token
                ↓
           Extract user ID
                ↓
          Search MongoDB
                ↓
        Read verified email
                ↓
       Determine backend role
                ↓
       Validate collection
                ↓
        Return current user

    The JWT role is NOT trusted.
    """

    # =====================================================
    # 1. Token must exist
    # =====================================================

    if not token:
        raise CREDENTIALS_EXCEPTION

    # =====================================================
    # 2. Decode JWT
    # =====================================================

    try:
        payload = decode_token(token)

        # Only access tokens can access protected APIs.
        if payload.get("type") != "access":
            raise CREDENTIALS_EXCEPTION

        user_id = payload.get("sub")

        if not user_id:
            raise CREDENTIALS_EXCEPTION

    except JWTError:
        raise CREDENTIALS_EXCEPTION

    except HTTPException:
        raise

    except Exception:
        raise CREDENTIALS_EXCEPTION

    # =====================================================
    # 3. Find account WITHOUT trusting JWT role
    # =====================================================

    user, collection_name = await _find_account_by_id(
        db=db,
        user_id=user_id,
    )

    if user is None or collection_name is None:
        raise CREDENTIALS_EXCEPTION

    # =====================================================
    # 4. Validate email
    # =====================================================

    email = user.get("email")

    if not email:
        raise CREDENTIALS_EXCEPTION

    email = str(email).strip().lower()

    # =====================================================
    # 5. Determine REAL role from backend config
    # =====================================================

    actual_role = _resolve_role_from_email(email)

    # =====================================================
    # 6. Verify that account is stored in the correct
    #    MongoDB collection
    # =====================================================

    if not _collection_matches_role(
        collection_name,
        actual_role,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account role configuration is invalid",
        )

    # =====================================================
    # 7. Check account status
    # =====================================================

    if user.get("is_active") is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # =====================================================
    # 8. Build safe current-user object
    # =====================================================

    user["_id"] = str(user["_id"])

    # NEVER expose password hash through current_user.
    user.pop("password_hash", None)

    # Backend-derived role is the ONLY role we expose.
    user["role"] = actual_role

    # Keep email normalized.
    user["email"] = email

    return user


# =========================================================
# ROLE-BASED ACCESS CONTROL
# =========================================================

def require_roles(*allowed_roles: str):
    """
    Route dependency factory.

    Example:

        Depends(require_roles("admin"))

    or:

        Depends(require_roles("partner"))

    or:

        Depends(require_roles("user", "admin"))
    """

    async def checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:

        actual_role = current_user.get("role")

        if actual_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_user

    return checker


# =========================================================
# CONVENIENCE ROLE DEPENDENCIES
# =========================================================

# Normal users only
require_user = require_roles("user")

# Partners only
require_partner = require_roles("partner")

# Institutions only
require_institution = require_roles("institution")

# Admin only
require_admin = require_roles("admin")


# =========================================================
# OPTIONAL: Admin + User Access
# =========================================================
#
# Keep this if some existing user endpoints are intentionally
# accessible to admins as well.
#
# Example:
#     Depends(require_user_or_admin)
#
# =========================================================

require_user_or_admin = require_roles(
    "user",
    "admin",
)


# =========================================================
# EXPORTS
# =========================================================

__all__ = [
    "oauth2_scheme",
    "CREDENTIALS_EXCEPTION",
    "get_current_user",
    "require_roles",
    "require_user",
    "require_partner",
    "require_institution",
    "require_admin",
    "require_user_or_admin",
]