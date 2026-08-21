import sys
import asyncio
from datetime import datetime, timezone

from pymongo import UpdateOne
from src.core.mongo import db # ទីតាំង Database របស់អ្នក
from src.core.security import hash_password # ត្រូវមាន Function នេះដើម្បីបង្កើត Password

async def migrate_fresh():
    print("🧹 Procesing Delete...")
    try:
        collection_names = await db.list_collection_names()
        if not collection_names:
            print("✨ Database is already empty!")
            return

        for coll_name in collection_names:
            await db.drop_collection(coll_name)
            print(f"  ❌ Has been deleted: {coll_name}")
            
        print("✅ Database has been reset successfully!")
    except Exception as e:
        print(f"[ERROR] Unexpected error in migrate_fresh: {e}")

async def seed_database():
    print("🌱 Seeding...")
    try:
        users_collection = db["users"]
        default_password = hash_password("password123")
        now = datetime.now(timezone.utc)

        seed_users = [
            {
                "first_name": "Super",
                "last_name": "Admin",
                "email": "roronoazoro11502@gmail.com",
                "password_hash": default_password,
                "auth_provider": "local",
                "role": "admin",
                "is_active": True,
                "is_profile_completed": True,
                "onboarding_completed": False,
                "verified_at": now,
                "created_at": now, 
                "updated_at": now
            },
            {
                "first_name": "Super",
                "last_name": "Admin",
                "email": "seatsatya@gmail.com",
                "password_hash": default_password,
                "auth_provider": "local",
                "role": "admin",
                "is_active": True,
                "is_profile_completed": True,
                "onboarding_completed": False,
                "verified_at": now,
                "created_at": now, 
                "updated_at": now
            },
            # {
            #     "first_name": "Super",
            #     "last_name": "Admin 3",
            #     "email": "seatsatya168@gmail.com",
            #     "password_hash": default_password,
            #     "auth_provider": "local",
            #     "role": "admin",
            #     "is_active": True,
            #     "is_profile_completed": True,
            #     "verified_at": now,
            #     "updated_at": now
            # },
            # {
            #     "first_name": "Super",
            #     "last_name": "Admin 3",
            #     "email": "test@gmail.com",
            #     "password_hash": default_password,
            #     "auth_provider": "local",
            #     "role": "admin",
            #     "is_active": True,
            #     "is_profile_completed": True,
            #     "verified_at": now,
            #     "updated_at": now
            # }, 
        ]

        # 🎯 ប្រើប្រាស់ Bulk Write និង Upsert
        operations = []
        for user in seed_users:
            # យក email ជាគោល សម្រាប់ឆែកថាតើ user នេះមានរួចរាល់ឬនៅ
            email_to_check = user.pop("email") 
            
            # ទាញយក និងលុប created_at ចេញពី $set បើវាមាន ដើម្បីការពារ Conflict ជាមួយ $setOnInsert
            user.pop("created_at", None)
            
            operations.append(
                UpdateOne(
                    {"email": email_to_check}, # លក្ខខណ្ឌស្វែងរក
                    {"$set": user, "$setOnInsert": {"email": email_to_check, "created_at": now}}, 
                    upsert=True # ឆែកផង បញ្ជូលផង ក្នុងពេលតែមួយ
                )
            )

        if operations:
            result = await users_collection.bulk_write(operations)
            print(f"✅ Success ! Added: {result.upserted_count}, Updated: {result.modified_count}")
        
    except Exception as e:
        print(f"[ERROR] Unexpected error in (Seed): {e}")

async def main():
    # 1. 🎯 ចាប់យកពាក្យបញ្ជាពី Terminal ដោយមិនយកឈ្មោះ File មកទេ
    args = sys.argv[1:] 

    if not args:
        print("❌ សូមបញ្ជាក់ជម្រើសណាមួយ! ឧទាហរណ៍៖")
        print("  - python manage_db.py reset  (Delete all collections and reset database)")
        print("  - python manage_db.py seed   (Add default users)")
        print("  - python manage_db.py fresh  (Delete all collections and add default users)")
        return

    # 2. 🎯 ដំណើរការទៅតាមពាក្យបញ្ជា
    if "reset" in args or "fresh" in args:
        await migrate_fresh()
        
    if "seed" in args or "fresh" in args:
        await seed_database()

if __name__ == "__main__":
    asyncio.run(main())