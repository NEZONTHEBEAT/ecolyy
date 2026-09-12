"""
Ecolyy MongoDB Database Configuration

Handles:
- MongoDB async connection using Motor
- Database initialization
- Connection health check
- Collection indexes
- FastAPI database dependency
"""

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
)

from app.core.config import settings


# =========================================================
# MONGODB STATE
# =========================================================

class MongoDB:
    """
    Stores the active MongoDB client and database instance.
    """

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


mongodb = MongoDB()


# =========================================================
# CONNECT TO MONGODB
# =========================================================

async def connect_to_mongo() -> None:
    """
    Connect to MongoDB and initialize required indexes.

    This function is called during FastAPI application startup.
    """

    # -----------------------------------------------------
    # Create MongoDB client
    # -----------------------------------------------------

    mongodb.client = AsyncIOMotorClient(
        settings.MONGO_URI,
        serverSelectionTimeoutMS=5000,
    )

    # -----------------------------------------------------
    # Test MongoDB connection
    # -----------------------------------------------------

    await mongodb.client.admin.command("ping")

    # -----------------------------------------------------
    # Select database
    # -----------------------------------------------------

    mongodb.db = mongodb.client[
        settings.MONGO_DB_NAME
    ]

    # =====================================================
    # USER / AUTH INDEXES
    # =====================================================

    await mongodb.db["users"].create_index(
        "email",
        unique=True,
    )

    await mongodb.db["partners"].create_index(
        "email",
        unique=True,
    )

    await mongodb.db["institutions"].create_index(
        "email",
        unique=True,
    )

    # =====================================================
    # PICKUP INDEXES
    # =====================================================

    await mongodb.db["pickups"].create_index(
        "user_id",
    )

    await mongodb.db["pickups"].create_index(
        "partner_id",
    )

    await mongodb.db["pickups"].create_index(
        "institution_id",
    )

    await mongodb.db["pickups"].create_index(
        "status",
    )

    # =====================================================
    # WALLET INDEXES
    # =====================================================

    await mongodb.db["wallets"].create_index(
        "user_id",
        unique=True,
    )

    # =====================================================
    # OTP INDEXES
    # =====================================================

    await mongodb.db["otps"].create_index(
        "email",
    )

    # Automatically delete expired OTP documents
    await mongodb.db["otps"].create_index(
        "expires_at",
        expireAfterSeconds=0,
    )

    # =====================================================
    # OPTIONAL COMMON INDEXES
    # =====================================================

    await mongodb.db["notifications"].create_index(
        "user_id",
    )

    await mongodb.db["rewards"].create_index(
        "is_active",
    )

    await mongodb.db["audit_logs"].create_index(
        "created_at",
    )

    print(
        f"✅ MongoDB connected: {settings.MONGO_DB_NAME}"
    )


# =========================================================
# CLOSE MONGODB CONNECTION
# =========================================================

async def close_mongo_connection() -> None:
    """
    Close MongoDB connection during application shutdown.
    """

    if mongodb.client is not None:
        mongodb.client.close()

        mongodb.client = None
        mongodb.db = None

        print("🔌 MongoDB connection closed")


# =========================================================
# FASTAPI DATABASE DEPENDENCY
# =========================================================

def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency that returns the active MongoDB database.

    Raises:
        RuntimeError:
            If MongoDB has not been initialized.
    """

    if mongodb.db is None:
        raise RuntimeError(
            "MongoDB is not connected. "
            "Make sure the application startup completed successfully."
        )

    return mongodb.db