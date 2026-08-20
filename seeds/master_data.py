from pymongo import UpdateOne, ASCENDING
from pymongo.errors import OperationFailure
from datetime import datetime, timezone
from src.core.mongo import (
    job_levels_collection,
    education_levels_collection,
    employment_types_collection,
    work_types_collection,
    industries_collection,
    skills_collection
)

# ១. រៀបចំទិន្នន័យ (Mock Data) សម្រាប់ Master Data នីមួយៗ
master_data_configs = [
    {
        "name": "Industries",
        "collection": industries_collection,
        "data": [
            {"name": "Information Technology", "is_active": True},
            {"name": "Banking & Finance", "is_active": True},
            {"name": "Healthcare & Medical", "is_active": True},
            {"name": "Education & Training", "is_active": True},
            {"name": "Real Estate & Construction", "is_active": True},
            {"name": "Manufacturing & Logistics", "is_active": True}
        ]
    },
    {
        "name": "Job Levels",
        "collection": job_levels_collection,
        "data": [
            {"name": "Entry Level", "is_active": True},
            {"name": "Junior", "is_active": True},
            {"name": "Mid-Level", "is_active": True},
            {"name": "Senior", "is_active": True},
            {"name": "Manager", "is_active": True},
            {"name": "Executive", "is_active": True},
            {"name": "Director", "is_active": True},
            {"name": "C-Level (CEO, CTO, etc.)", "is_active": True}
        ]
    },
    {
        "name": "Education Levels",
        "collection": education_levels_collection,
        "data": [
            {"name": "High School", "is_active": True},
            {"name": "Vocational Training", "is_active": True},
            {"name": "Associate Degree", "is_active": True},
            {"name": "Bachelor's Degree", "is_active": True},
            {"name": "Master's Degree", "is_active": True},
            {"name": "Doctorate (PhD)", "is_active": True}
        ]
    },
    {
        "name": "Employment Types",
        "collection": employment_types_collection,
        "data": [
            {"name": "Full-Time", "is_active": True},
            {"name": "Part-Time", "is_active": True},
            {"name": "Contract", "is_active": True},
            {"name": "Freelance", "is_active": True},
            {"name": "Internship", "is_active": True},
            {"name": "Temporary", "is_active": True},
            {"name": "Volunteer", "is_active": True}
        ]
    },
    {
        "name": "Work Types",
        "collection": work_types_collection,
        "data": [
            {"name": "On-site", "is_active": True},
            {"name": "Remote", "is_active": True},
            {"name": "Hybrid", "is_active": True},
            {"name": "Field Work", "is_active": True}
        ]
    },
    {
        "name": "Skills",
        "collection": skills_collection,
        "data": [
            {"name": "Python", "is_active": True},
            {"name": "JavaScript", "is_active": True},
            {"name": "Flutter", "is_active": True},
            {"name": "React", "is_active": True},
            {"name": "Node.js", "is_active": True},
            {"name": "SQL", "is_active": True},
            {"name": "MongoDB", "is_active": True},
            {"name": "Data Analysis", "is_active": True},
            {"name": "UI/UX Design", "is_active": True},
            {"name": "Digital Marketing", "is_active": True},
            {"name": "Project Management", "is_active": True},
            {"name": "Communication", "is_active": True},
            {"name": "Problem Solving", "is_active": True},
            {"name": "Team Leadership", "is_active": True},
            {"name": "Time Management", "is_active": True}
        ]
    }
]

# ២. Function រួមសម្រាប់រត់បញ្ចូលទិន្នន័យទាំងអស់
async def seed_master_data():
    print("⏳ Starting Master Data Seeding...")
    
    now = datetime.now(timezone.utc)
    
    for config in master_data_configs:
        collection_name = config["name"]
        collection = config["collection"]
        data_list = config["data"]
        
        print(f"  -> Checking and Creating {collection_name}...")
        
        if not data_list:
            continue

        # ចាប់យក Error បើមានបញ្ហាក្នុងការបង្កើត Index (ការពារកុំឱ្យគាំង Script ទាំងមូល)
        try:
            # ប្រើទម្រង់ [("name", ASCENDING)] ជំនួសឱ្យ "name" ទទេ
            await collection.create_index([("name", ASCENDING)], unique=True)
        except OperationFailure as e:
            print(f"     ⚠️ មិនអាចបង្កើត Index ថ្មីបានទេ (អាចមាន Index ចាស់រួចហើយ): {e.details.get('errmsg', str(e))}")
            print(f"     👉 កំពុងព្យាយាមលុប Index ចាស់ `name_1` ហើយបង្កើតថ្មី...")
            try:
                await collection.drop_index("name_1")
                await collection.create_index([("name", ASCENDING)], unique=True)
                print(f"     ✅ ដោះស្រាយ និងបង្កើត Index `unique` បានជោគជ័យ!")
            except Exception as drop_e:
                print(f"     ❌ បរាជ័យទាំងស្រុងក្នុងការបង្កើត Index: {drop_e}")
        except Exception as e:
            print(f"     ❌ មានបញ្ហាក្នុងការភ្ជាប់ទៅ Database (សូមឆែក .env ឬ IP Whitelist): {e}")
            return # បញ្ឈប់ការរត់ Script បើភ្ជាប់ Database មិនបាន

        operations = []
        
        # ប្រើ enumerate ដើម្បីបង្កើត order ស្វ័យប្រវត្តិតាមលំដាប់នៃបញ្ជីទិន្នន័យ[cite: 3]
        for index, item in enumerate(data_list, start=1):
            
            # កែមកប្រើ Field `order` វិញតាម Schema[cite: 3]
            item["order"] = index
            
            op = UpdateOne(
                {"name": item["name"]},
                {
                    "$set": {
                        **item,
                        "updated_at": now
                    },
                    "$setOnInsert": {
                        "created_at": now
                    }
                },          
                upsert=True
            )
            operations.append(op)
        
        # រត់បញ្ជូលទិន្នន័យដោយប្រើ bulk_write[cite: 3]
        if operations:
            result = await collection.bulk_write(operations)
            print(f"  ✅ {collection_name} -> Add New: {result.upserted_count} | Update: {result.modified_count}")
        
    print("🎉 All Master Data Seeded Successfully!")