"""
/api/v1/users — the logged-in customer's own profile & addresses.
(Wallet lives in wallet.py, notifications live in notifications.py.)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.permissions import get_current_user, require_user
from app.models.address import AddressModel
from app.schemas.user import AddressCreate, UserUpdate
from app.utils.helpers import serialize_doc, to_object_id

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return serialize_doc(current_user)


@router.patch("/me")
async def update_me(payload: UserUpdate, current_user: dict = Depends(require_user),
                     db: AsyncIOMotorDatabase = Depends(get_database)):
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if updates:
        await db["users"].update_one({"_id": to_object_id(current_user["_id"])}, {"$set": updates})
    updated = await db["users"].find_one({"_id": to_object_id(current_user["_id"])})
    return serialize_doc(updated)


@router.get("/me/addresses")
async def list_addresses(current_user: dict = Depends(require_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    cursor = db["addresses"].find({"user_id": current_user["_id"]}).sort("created_at", -1)
    return [serialize_doc(doc) async for doc in cursor]


@router.post("/me/addresses")
async def add_address(payload: AddressCreate, current_user: dict = Depends(require_user),
                       db: AsyncIOMotorDatabase = Depends(get_database)):
    doc = AddressModel.new(user_id=current_user["_id"], **payload.model_dump())
    result = await db["addresses"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize_doc(doc)


@router.delete("/me/addresses/{address_id}")
async def delete_address(address_id: str, current_user: dict = Depends(require_user),
                          db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db["addresses"].delete_one({"_id": to_object_id(address_id), "user_id": current_user["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Address not found")
    return {"message": "Address deleted"}
