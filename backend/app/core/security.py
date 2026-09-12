"""
=========================================================
Ecolyy - Security Utilities
=========================================================

Handles:

- Password hashing
- Password verification
- Access JWT creation
- Refresh JWT creation
- JWT decoding

IMPORTANT:
- Never store plain-text passwords.
- Never expose password hashes to frontend.
- JWT role is only a token claim.
- Backend permissions.py re-validates the real role
  from the account email.
=========================================================
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# =========================================================
# PASSWORD HASHING
# =========================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    """

    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.
    """

    if not plain_password or not hashed_password:
        return False

    try:
        return pwd_context.verify(
            plain_password,
            hashed_password,
        )

    except Exception:
        return False


# =========================================================
# ACCESS TOKEN
# =========================================================

def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived access JWT.

    `subject` should normally be the MongoDB user ID.

    Additional claims such as role may be included, but
    permissions.py does NOT blindly trust the role claim.
    """

    now = datetime.now(timezone.utc)

    expire = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "jti": str(uuid4()),
        "type": "access",
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


# =========================================================
# REFRESH TOKEN
# =========================================================

def create_refresh_token(
    subject: str,
) -> str:
    """
    Create a long-lived refresh JWT.

    IMPORTANT:

    Refresh tokens intentionally contain NO role.

    The role is re-derived from MongoDB/email whenever
    a new access token is generated.
    """

    now = datetime.now(timezone.utc)

    expire = now + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "jti": str(uuid4()),
        "type": "refresh",
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


# =========================================================
# DECODE JWT
# =========================================================

def decode_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    python-jose automatically validates:
        - Signature
        - Expiration
        - Algorithm

    Raises:
        jose.JWTError
    """

    if not token or not isinstance(token, str):
        raise JWTError("Invalid token")

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


# =========================================================
# EXPORTS
# =========================================================

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "JWTError",
]