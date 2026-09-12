"""Credits/debits a user's wallet and records a transaction, atomically enough for our needs."""
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.wallet import WalletTransactionModel
from app.utils.helpers import to_object_id, utcnow


async def credit_wallet(db: AsyncIOMotorDatabase, user_id: str, amount: float, reason: str, reference_id: str | None = None) -> None:
    wallet = await db["wallets"].find_one({"user_id": user_id})
    if not wallet:
        from app.models.wallet import WalletModel
        wallet = WalletModel.new(user_id)
        result = await db["wallets"].insert_one(wallet)
        wallet["_id"] = result.inserted_id

    await db["wallets"].update_one(
        {"_id": wallet["_id"]},
        {"$inc": {"balance": amount}, "$set": {"updated_at": utcnow()}},
    )
    tx = WalletTransactionModel.new(str(wallet["_id"]), user_id, "credit", amount, reason, reference_id)
    await db["wallet_transactions"].insert_one(tx)


async def debit_wallet(db: AsyncIOMotorDatabase, user_id: str, amount: float, reason: str, reference_id: str | None = None) -> bool:
    wallet = await db["wallets"].find_one({"user_id": user_id})
    if not wallet or wallet.get("balance", 0) < amount:
        return False
    await db["wallets"].update_one(
        {"_id": wallet["_id"]},
        {"$inc": {"balance": -amount}, "$set": {"updated_at": utcnow()}},
    )
    tx = WalletTransactionModel.new(str(wallet["_id"]), user_id, "debit", amount, reason, reference_id)
    await db["wallet_transactions"].insert_one(tx)
    return True


async def get_wallet(db: AsyncIOMotorDatabase, user_id: str) -> dict | None:
    return await db["wallets"].find_one({"user_id": user_id})


async def list_transactions(db: AsyncIOMotorDatabase, user_id: str) -> list[dict]:
    cursor = db["wallet_transactions"].find({"user_id": user_id}).sort("created_at", -1)
    return [doc async for doc in cursor]
