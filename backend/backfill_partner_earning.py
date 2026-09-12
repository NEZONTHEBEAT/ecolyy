import asyncio

from bson import ObjectId

from app.core.database import (
    mongodb,
    connect_to_mongo,
    close_mongo_connection,
)


PICKUP_ID = "6a9cbea8622bdeb34147bee6"
PARTNER_EARNING = 50.0


async def main():
    try:
        await connect_to_mongo()

        pickup_object_id = ObjectId(PICKUP_ID)

        result = await mongodb.db["pickups"].update_one(
            {
                "_id": pickup_object_id
            },
            {
                "$set": {
                    "partner_earning": PARTNER_EARNING
                }
            }
        )

        print("✅ Backfill completed")
        print("Matched:", result.matched_count)
        print("Modified:", result.modified_count)

        pickup = await mongodb.db["pickups"].find_one(
            {
                "_id": pickup_object_id
            }
        )

        if pickup:
            print(
                "Pickup ID:",
                str(pickup["_id"])
            )

            print(
                "Partner earning:",
                pickup.get("partner_earning")
            )
        else:
            print("❌ Pickup not found")

    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())

