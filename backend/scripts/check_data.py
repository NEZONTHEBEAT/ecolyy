import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_data():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["ecolyy"]
    
    # Check partners
    partner = await db.partners.find_one({"email": "himanshu.b.11231@gmail.com"})
    if partner:
        print("Partner found!")
        print(f"   Name: {partner['name']}")
        print(f"   Email: {partner['email']}")
        print(f"   Password Hash: {partner['password_hash'][:20]}...")
    else:
        print("Partner not found! Please insert data.")
    
    # Check institutions
    institution = await db.institutions.find_one({"email": "shamik.b.1123@inspiria.edu.in"})
    if institution:
        print("\n Institution found!")
        print(f"   Name: {institution['name']}")
        print(f"   Email: {institution['email']}")
        print(f"   Password Hash: {institution['password_hash'][:20]}...")
    else:
        print("\n Institution not found! Please insert data.")

if __name__ == "__main__":
    asyncio.run(check_data())