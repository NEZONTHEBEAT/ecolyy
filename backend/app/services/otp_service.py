"""
OTP generation/verification, stored in the `otps` collection with a TTL index
(see core/database.py) so expired codes are auto-deleted by MongoDB.

Swap `_send_otp_email` for a real provider (see email_service.py) when ready.
"""
import random
from datetime import timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.services.email_service import send_email
from app.utils.helpers import utcnow


def _generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"


async def request_otp(db: AsyncIOMotorDatabase, email: str) -> None:
    code = _generate_code()
    await db["otps"].update_one(
        {"email": email.lower()},
        {
            "$set": {
                "email": email.lower(),
                "code": code,
                "expires_at": utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
                "verified": False,
            }
        },
        upsert=True,
    )
    await send_email(
        to=email,
        subject="Your ReKart verification code",
        body=f"Your OTP is {code}. It expires in {settings.OTP_EXPIRE_MINUTES} minutes.",
    )


async def verify_otp(db: AsyncIOMotorDatabase, email: str, code: str) -> bool:
    record = await db["otps"].find_one({"email": email.lower()})
    if not record:
        return False
    if record.get("code") != code:
        return False
    if record.get("expires_at") and record["expires_at"] < utcnow():
        return False
    await db["otps"].update_one({"email": email.lower()}, {"$set": {"verified": True}})
    return True
