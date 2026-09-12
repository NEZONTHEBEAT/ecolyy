"""
=========================================================
Ecolyy - Authentication API
=========================================================

Endpoints:

POST /auth/register
POST /auth/login
POST /auth/google
POST /auth/otp/request
POST /auth/otp/verify
POST /auth/refresh
GET  /auth/detect-role

ROLE RULES
---------------------------------------------------------
ADMIN
    neelspunkryderz71@gmail.com
    -> Google Sign-In only

PARTNER
    himanshu.b.11231@gmail.com
    -> Email + Password only

INSTITUTION
    shamik.b.1123@inspiria.edu.in
    -> Email + Password only

USER
    Any other email
    -> Google Sign-In / Email OTP

IMPORTANT
---------------------------------------------------------
- Frontend never decides the role.
- Backend determines the role from the email.
- Frontend role selectors are NOT trusted.
- JWT role is revalidated from the account email.
=========================================================
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.database import get_database
from app.core.security import (
    JWTError,
    create_access_token,
    decode_token,
)

from app.models.user import UserModel
from app.models.wallet import WalletModel

from app.schemas.auth import (
    GoogleLoginRequest,
    LoginRequest,
    OTPRequest,
    OTPVerifyRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)

from app.services import auth_service, otp_service


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


# =========================================================
# REGISTER
# =========================================================

@router.post(
    "/register",
    response_model=TokenResponse,
)
async def register(
    payload: RegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Public registration.

    Only normal USER accounts can register publicly.

    Admin / Partner / Institution accounts are controlled
    accounts and cannot self-register.
    """

    try:

        return await auth_service.register(
            db=db,
            name=payload.name,
            email=payload.email,
            password=payload.password,
            phone=payload.phone,
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(f"Registration error: {exc}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )


# =========================================================
# PASSWORD LOGIN
# =========================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    payload: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Password login.

    Allowed:
        Partner
        Institution

    Not allowed:
        Admin
        User
    """

    try:

        return await auth_service.login(
            db=db,
            email=payload.email,
            password=payload.password,
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(f"Login error: {exc}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again.",
        )


# =========================================================
# GOOGLE LOGIN
# =========================================================

@router.post(
    "/google",
    response_model=TokenResponse,
)
async def google_login(
    payload: GoogleLoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Google Sign-In.

    Allowed:
        Admin
        User

    Partner and Institution must use password login.
    """

    try:

        return await auth_service.google_login(
            db=db,
            id_token_str=payload.id_token,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    except HTTPException:
        raise

    except Exception as exc:

        print(f"Google login error: {exc}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Sign-In failed. Please try again.",
        )


# =========================================================
# OTP REQUEST
# =========================================================

@router.post(
    "/otp/request",
)
async def request_otp(
    payload: OTPRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Request an Email OTP.

    OTP authentication is only available for
    normal USER accounts.
    """

    email = str(payload.email).strip().lower()

    # -----------------------------------------------------
    # Backend determines role
    # -----------------------------------------------------

    role = settings.detect_role_from_email(
        email
    )

    # -----------------------------------------------------
    # Only normal users can use OTP
    # -----------------------------------------------------

    if role != "user":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "OTP login is available only for normal "
                "user accounts."
            ),
        )

    try:

        await otp_service.request_otp(
            db,
            email,
        )

    except Exception as exc:

        print(f"OTP request error: {exc}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send OTP. Please try again.",
        )

    return {
        "message": "OTP sent successfully",
    }


# =========================================================
# OTP VERIFY
# =========================================================

@router.post(
    "/otp/verify",
    response_model=TokenResponse,
)
async def verify_otp(
    payload: OTPVerifyRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Verify Email OTP and issue JWT tokens.

    OTP authentication is only available for
    normal USER accounts.
    """

    email = str(payload.email).strip().lower()

    # -----------------------------------------------------
    # Backend determines role
    # -----------------------------------------------------

    role = settings.detect_role_from_email(
        email
    )

    if role != "user":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "OTP login is available only for normal "
                "user accounts."
            ),
        )

    # -----------------------------------------------------
    # Verify OTP
    # -----------------------------------------------------

    try:

        verified = await otp_service.verify_otp(
            db,
            email,
            payload.code,
        )

    except Exception as exc:

        print(f"OTP verification error: {exc}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP verification failed. Please try again.",
        )

    if not verified:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    # -----------------------------------------------------
    # Find existing account
    # -----------------------------------------------------

    doc, collection_name = (
        await auth_service.find_account_by_email(
            db,
            email,
        )
    )

    # -----------------------------------------------------
    # Create USER account if not found
    # -----------------------------------------------------

    if not doc:

        name = (
            payload.name.strip()
            if payload.name
            else email.split("@")[0]
        )

        doc = UserModel.new(
            name=name,
            email=email,
            phone=None,
            password_hash=None,
            google_id=None,
            role="user",
        )

        doc["is_verified"] = True

        result = await db["users"].insert_one(
            doc
        )

        doc["_id"] = result.inserted_id

        # Create wallet for new normal user
        await db["wallets"].insert_one(
            WalletModel.new(
                str(doc["_id"])
            )
        )

    # -----------------------------------------------------
    # Existing account
    # -----------------------------------------------------

    else:

        if collection_name != "users":

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account role configuration is invalid",
            )

        if doc.get("is_active") is False:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        updates = {
            "is_verified": True,
            "role": "user",
            "updated_at": datetime.now(
                timezone.utc
            ),
        }

        if payload.name:

            clean_name = payload.name.strip()

            if clean_name:
                updates["name"] = clean_name

        await db["users"].update_one(
            {
                "_id": doc["_id"],
            },
            {
                "$set": updates,
            },
        )

        doc.update(updates)

    # -----------------------------------------------------
    # Issue JWT tokens
    # -----------------------------------------------------

    return auth_service._issue_tokens(
        str(doc["_id"]),
        "user",
        doc,
    )


# =========================================================
# REFRESH TOKEN
# =========================================================

@router.post(
    "/refresh",
)
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Generate a new access token from a valid refresh token.

    IMPORTANT:
        The role is NEVER trusted from the JWT.

    Role is derived again from the account email.
    """

    # =====================================================
    # 1. Decode token
    # =====================================================

    try:

        data = decode_token(
            payload.refresh_token
        )

        if data.get("type") != "refresh":

            raise ValueError(
                "Not a refresh token"
            )

        user_id = data.get("sub")

        if not user_id:

            raise ValueError(
                "Invalid refresh token"
            )

    except (JWTError, ValueError):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # =====================================================
    # 2. Convert ObjectId
    # =====================================================

    try:

        object_id = ObjectId(
            user_id
        )

    except (InvalidId, TypeError):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # =====================================================
    # 3. Find account
    # =====================================================

    account = None
    collection_name = None

    for name in (
        "users",
        "partners",
        "institutions",
    ):

        candidate = await db[name].find_one(
            {
                "_id": object_id,
            }
        )

        if candidate:

            account = candidate
            collection_name = name
            break

    # =====================================================
    # 4. Account not found
    # =====================================================

    if account is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
        )

    # =====================================================
    # 5. Account disabled
    # =====================================================

    if account.get("is_active") is False:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # =====================================================
    # 6. Email validation
    # =====================================================

    email = account.get("email")

    if not email:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account email is missing",
        )

    email = str(email).strip().lower()

    # =====================================================
    # 7. Recalculate authoritative role
    # =====================================================

    role = settings.detect_role_from_email(
        email
    )

    # =====================================================
    # 8. Validate collection
    # =====================================================

    expected_collection = {
        "user": "users",
        "admin": "users",
        "partner": "partners",
        "institution": "institutions",
    }.get(role)

    if expected_collection != collection_name:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account role configuration is invalid",
        )

    # =====================================================
    # 9. Create new access token
    # =====================================================

    access_token = create_access_token(
        subject=str(account["_id"]),
        extra_claims={
            "role": role,
        },
    )

    # =====================================================
    # 10. Response
    # =====================================================

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role,
    }


# =========================================================
# DETECT ROLE
# =========================================================

@router.get(
    "/detect-role",
)
async def detect_role(
    email: str,
):
    """
    Public helper for frontend UX.

    IMPORTANT:
        This endpoint does NOT authenticate anyone.
        It is only a UI hint.

    Actual authentication and authorization are always
    handled by the backend.
    """

    email = email.strip().lower()

    role = settings.detect_role_from_email(
        email
    )

    return {
        "email": email,
        "role": role,
        "display_role": settings.get_display_role(
            role
        ),
        "redirect_url": settings.get_redirect_url_for_role(
            role
        ),
        "is_admin": settings.is_admin_email(
            email
        ),
        "is_partner": settings.is_partner_email(
            email
        ),
        "is_institute": settings.is_institute_email(
            email
        ),
    }