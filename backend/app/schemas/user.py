from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str
    points: int
    avatar_url: Optional[str] = None
    is_verified: bool
    created_at: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class AddressCreate(BaseModel):
    label: str
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    is_default: bool = False


class AddressOut(AddressCreate):
    id: str
