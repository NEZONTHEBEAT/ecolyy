from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# =========================================================
# REGISTER
# =========================================================

class RegisterRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128,
    )

    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=20,
    )


# =========================================================
# PASSWORD LOGIN
# =========================================================

class LoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128,
    )


# =========================================================
# GOOGLE AUTH
# =========================================================

class GoogleLoginRequest(BaseModel):
    id_token: str = Field(
        min_length=10,
    )


# =========================================================
# EMAIL OTP
# =========================================================

class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerifyRequest(BaseModel):
    email: EmailStr

    code: str = Field(
        min_length=6,
        max_length=6,
    )

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )


# =========================================================
# OPTIONAL EXPLICIT EMAIL OTP SCHEMAS
# =========================================================

class EmailOTPRequest(BaseModel):
    email: EmailStr


class EmailOTPVerifyRequest(BaseModel):
    email: EmailStr

    code: str = Field(
        min_length=6,
        max_length=6,
    )

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )


# =========================================================
# PHONE OTP
# =========================================================

class PhoneOTPRequest(BaseModel):
    phone: str = Field(
        min_length=10,
        max_length=20,
    )


class PhoneOTPVerifyRequest(BaseModel):
    phone: str = Field(
        min_length=10,
        max_length=20,
    )

    code: str = Field(
        min_length=6,
        max_length=6,
    )

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )


# =========================================================
# TOKEN REFRESH
# =========================================================

class RefreshRequest(BaseModel):
    refresh_token: str


# =========================================================
# TOKEN RESPONSE
# =========================================================

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    user: dict