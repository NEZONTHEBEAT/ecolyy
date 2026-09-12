"""
Collection: wallets
{ _id, user_id (unique), balance, currency, created_at, updated_at }

Collection: wallet_transactions
{ _id, wallet_id, user_id, type ("credit"|"debit"), amount, reason,
  reference_id (e.g. pickup_id), created_at }
"""
from datetime import datetime, timezone


class WalletModel:
    collection_name = "wallets"

    @staticmethod
    def new(user_id: str) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "user_id": user_id,
            "balance": 0.0,
            "currency": "INR",
            "created_at": now,
            "updated_at": now,
        }


class WalletTransactionModel:
    collection_name = "wallet_transactions"

    @staticmethod
    def new(wallet_id: str, user_id: str, tx_type: str, amount: float, reason: str, reference_id: str | None = None) -> dict:
        return {
            "wallet_id": wallet_id,
            "user_id": user_id,
            "type": tx_type,
            "amount": amount,
            "reason": reason,
            "reference_id": reference_id,
            "created_at": datetime.now(timezone.utc),
        }
