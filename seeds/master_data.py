from pymongo import UpdateOne
from src.core.mongo import (
    job_levels_collection,
    education_levels_collection,
    employment_types_collection,
    work_types_collection
)

# ១. រៀបចំទិន្នន័យ (Mock Data) សម្រាប់ Master Data នីមួយៗ
master_data_configs = [
    {
        "name": "Job Levels",
        "collection": job_levels_collection,
        "data": [
            {"name": "Entry Level", "order": 1, "is_active": True},
            {"name": "Junior", "order": 2, "is_active": True},
            {"name": "Mid-Level", "order": 3, "is_active": True},
            {"name": "Senior", "order": 4, "is_active": True},
            {"name": "Manager", "order": 5, "is_active": True},
            {"name": "Executive", "order": 6, "is_active": True}
        ]
    },
    {
        "name": "Education Levels",
        "collection": education_levels_collection,
        "data": [
            {"name": "High School", "order": 1, "is_active": True},
            {"name": "Associate Degree", "order": 2, "is_active": True},
            {"name": "Bachelor's Degree", "order": 3, "is_active": True},
            {"name": "Master's Degree", "order": 4, "is_active": True},
            {"name": "Doctorate (PhD)", "order": 5, "is_active": True}
        ]
    },
    {
        "name": "Employment Types",
        "collection": employment_types_collection,
        "data": [
            {"name": "Full-Time", "order": 1, "is_active": True},
            {"name": "Part-Time", "order": 2, "is_active": True},
            {"name": "Contract", "order": 3, "is_active": True},
            {"name": "Freelance", "order": 4, "is_active": True},
            {"name": "Internship", "order": 5, "is_active": True}
        ]
    },
    {
        "name": "Work Types",
        "collection": work_types_collection,
        "data": [
            {"name": "On-site", "order": 1, "is_active": True},
            {"name": "Remote", "order": 2, "is_active": True},
            {"name": "Hybrid", "order": 3, "is_active": True}
        ]
    }
]

# ២. Function រួមសម្រាប់រត់បញ្ចូលទិន្នន័យទាំងអស់
async def seed_master_data():
    print("⏳ Starting Master Data Seeding...")
    
    for config in master_data_configs:
        collection_name = config["name"]
        collection = config["collection"]
        data_list = config["data"]
        
        print(f"  -> Checking and Creating {collection_name}...")
        
        if not data_list:
            continue

        operations = []
        for item in data_list:
            op = UpdateOne(
                {"name": item["name"]},  # ស្វែងរកតាមឈ្មោះ
                {"$set": item},          # អាប់ដេតបើមានស្រាប់
                upsert=True              # បង្កើតថ្មីបើគ្មាន
            )
            operations.append(op)
        
        # អនុវត្តប្រតិបត្តិការសម្រាប់ Collection នីមួយៗ
        result = await collection.bulk_write(operations)
        print(f"  ✅ {collection_name} -> Add New: {result.upserted_count} | Update: {result.modified_count}")
        
    print("🎉 All Master Data Seeded Successfully!")