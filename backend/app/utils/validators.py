"""Reusable validation helpers not already covered by pydantic types."""
import re

PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")
PINCODE_RE = re.compile(r"^[0-9]{4,10}$")


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_RE.match(phone))


def is_valid_pincode(pincode: str) -> bool:
    return bool(PINCODE_RE.match(pincode))


def is_super_admin_email(email: str, super_admin_email: str) -> bool:
    """Case-insensitive exact match — the ONLY email allowed the admin role."""
    return email.strip().lower() == super_admin_email.strip().lower()
