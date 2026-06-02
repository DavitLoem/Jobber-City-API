import sys
import asyncio
from datetime import datetime, timezone
from src.core.mongo import db # ទីតាំង Database របស់អ្នក
from src.core.security import hash_password # ត្រូវមាន Function នេះដើម្បីបង្កើត Password

async def migrate_fresh():
    print("🧹 កំពុងដំណើរការ លុបទិន្នន័យ (Reset)...")
    try:
        collection_names = await db.list_collection_names()
        if not collection_names:
            print("✨ Database របស់អ្នកទទេស្អាតស្រាប់ហើយ!")
            return

        for coll_name in collection_names:
            await db.drop_collection(coll_name)
            print(f"  ❌ Has been deleted: {coll_name}")
            
        print("✅ Database has been reset successfully!")
    except Exception as e:
        print(f"[ERROR] Unexpected error in migrate_fresh: {e}")

async def seed_database():
    print("🌱 កំពុងបញ្ជូលទិន្នន័យសាកល្បង (Seeding)...")
    try:
        users_collection = db["users"]
        
        # 🎯 ការពារការបញ្ជូលទិន្នន័យជាន់គ្នា (បើគាត់វាយ command seed ច្រើនដង)
        existing_admin = await users_collection.find_one({"email": "admin@app.com"})
        if existing_admin:
            print("⚠️ ទិន្នន័យមានរួចរាល់ហើយ! មិនចាំបាច់ Seed ម្ដងទៀតទេ។ (Password: password123)")
            return

        # កំណត់ Password រួមមួយសម្រាប់ងាយស្រួល Test
        default_password = hash_password("password123")
        now = datetime.now(timezone.utc)

        # បង្កើតទិន្នន័យគណនីតេស្តទៅតាម Role នីមួយៗ
        seed_users = [
            {
                "name": "Super Admin",
                "email": "roronoazoro11502@gmail.com",
                "password_hash": default_password,
                "auth_provider": "local",
                "role": "admin",
                "is_active": True,
                "is_profile_completed": True,
                "verified_at": now,
                "created_at": now,
                "updated_at": now
            },
        ]

        # បញ្ចូលទិន្នន័យទាំងអស់ទៅក្នុង Database ក្នុងពេលតែមួយ
        await users_collection.insert_many(seed_users)
        print("✅ ជោគជ័យ! ទិន្នន័យ Admin, Employer និង Employee ត្រូវបានបញ្ជូល។ (Password: password123)")
        
    except Exception as e:
        print(f"មានបញ្ហាក្នុងការបញ្ជូលទិន្នន័យ (Seed): {e}")

async def main():
    # 1. 🎯 ចាប់យកពាក្យបញ្ជាពី Terminal ដោយមិនយកឈ្មោះ File មកទេ
    args = sys.argv[1:] 

    if not args:
        print("❌ សូមបញ្ជាក់ជម្រើសណាមួយ! ឧទាហរណ៍៖")
        print("  - python manage_db.py reset  (លុបទិន្នន័យចោលទាំងអស់)")
        print("  - python manage_db.py seed   (គ្រាន់តែបញ្ជូល Data តេស្ត ដោយមិនលុបទិន្នន័យចាស់)")
        print("  - python manage_db.py fresh  (លុបចោលទាំងអស់ រួចបញ្ជូល Data តេស្តថ្មី)")
        return

    # 2. 🎯 ដំណើរការទៅតាមពាក្យបញ្ជា
    if "reset" in args or "fresh" in args:
        await migrate_fresh()
        
    if "seed" in args or "fresh" in args:
        await seed_database()

if __name__ == "__main__":
    asyncio.run(main())