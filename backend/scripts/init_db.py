import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def init_database():
    # MongoDB connection
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["ecolyy"]
    
    print("Creating database and collections...")
    print("-" * 50)
    
    # =============================================
    # 1. Create Collections
    # =============================================
    collections = ["users", "partners", "institutions", "wallets", "pickups"]
    
    for collection_name in collections:
        try:
            # Check if collection exists
            existing = await db.list_collection_names()
            if collection_name not in existing:
                await db.create_collection(collection_name)
                print(f"Collection created: {collection_name}")
            else:
                print(f"Collection already exists: {collection_name}")
        except Exception as e:
            print(f"Error creating {collection_name}: {e}")
    
    print("-" * 50)
    
    # =============================================
    # 2. Insert Partner Data
    # =============================================
    partner_data = {
        "name": "EcoRecycle Ltd",
        "email": "himanshu.b.11231@gmail.com",
        "password_hash": get_password_hash("partner123"),
        "phone": "+91 9876543210",
        "partner_id": "PRT-001",
        "service_area": "Siliguri",
        "verification_status": "verified",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    existing = await db.partners.find_one({"email": partner_data["email"]})
    if not existing:
        result = await db.partners.insert_one(partner_data)
        print(f"Partner created: {result.inserted_id}")
        print(f"   Email: {partner_data['email']}")
        print(f"   Password: partner123")
    else:
        print("Partner already exists")
    
    # =============================================
    # 3. Insert Institution Data
    # =============================================
    institution_data = {
        "name": "Inspiria Institute",
        "email": "shamik.b.1123@inspiria.edu.in",
        "password_hash": get_password_hash("institute123"),
        "phone": "+91 9876543210",
        "institute_id": "INS-001",
        "type": "college",
        "address": "Siliguri, West Bengal",
        "verification_status": "verified",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    existing = await db.institutions.find_one({"email": institution_data["email"]})
    if not existing:
        result = await db.institutions.insert_one(institution_data)
        print(f"Institution created: {result.inserted_id}")
        print(f"   Email: {institution_data['email']}")
        print(f"   Password: institute123")
    else:
        print("Institution already exists")
    
    # =============================================
    # 4. Insert Admin User (if not exists)
    # =============================================
    admin_data = {
        "name": "Admin",
        "email": "neelspunkryderz71@gmail.com",
        "password_hash": get_password_hash("admin123"),
        "phone": "+91 9876543210",
        "role": "admin",
        "is_verified": True,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    existing = await db.users.find_one({"email": admin_data["email"]})
    if not existing:
        result = await db.users.insert_one(admin_data)
        print(f"Admin created: {result.inserted_id}")
        print(f"   Email: {admin_data['email']}")
        print(f"   Password: admin123")
    else:
        print("Admin already exists")
    
    # =============================================
    # 5. Summary
    # =============================================
    print("-" * 50)
    print("\n Database Summary:")
    print("-" * 50)
    
    users = await db.users.find().to_list(length=10)
    partners = await db.partners.find().to_list(length=10)
    institutions = await db.institutions.find().to_list(length=10)
    
    print(f" Users: {len(users)}")
    for u in users:
        print(f"  - {u['name']} ({u['email']}) - {u.get('role', 'user')}")
    
    print(f"\n Partners: {len(partners)}")
    for p in partners:
        print(f"  - {p['name']} ({p['email']})")
    
    print(f"\n Institutions: {len(institutions)}")
    for i in institutions:
        print(f"  - {i['name']} ({i['email']})")
    
    print("\n" + "=" * 50)
    print("Database initialization completed!")
    print("=" * 50)
    
    print("\n Login Credentials:")
    print("-" * 30)
    print("Admin: neelspunkryderz71@gmail.com / admin123")
    print("Partner: himanshu.b.11231@gmail.com / partner123")
    print("Institute: shamik.b.1123@inspiria.edu.in / institute123")
    print("User: user@ecolyy.com / user123")

if __name__ == "__main__":
    asyncio.run(init_database())