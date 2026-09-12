"""
/api/v1/wallet — the logged-in user's wallet balance and transaction history.
Money is credited automatically by pickup_service.update_status() when a
pickup is marked "completed" — this router only exposes read access
(no direct debit/credit endpoint; redemptions go through /rewards/redeem).
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.permissions import require_user
from app.services import wallet_service
from app.utils.helpers import serialize_doc

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/me")
async def get_my_wallet(current_user: dict = Depends(require_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    wallet = await wallet_service.get_wallet(db, current_user["_id"])
    return serialize_doc(wallet)


@router.get("/me/transactions")
async def get_my_transactions(current_user: dict = Depends(require_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    transactions = await wallet_service.list_transactions(db, current_user["_id"])
    return [serialize_doc(t) for t in transactions]
