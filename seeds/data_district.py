from pymongo import UpdateOne
from src.core.mongo import districts_collection

# (ទិន្នន័យ districts_data គឺនៅរក្សាដដែល)
districts_data = [
    {
        "province_id": "6a3cf688de300298e7b3096e", 
        "name_en": "Daun Penh", 
        "name_km": "ដូនពេញ", 
        "sort_order": 1, 
        "is_active": True
    },
    {
        "province_id": "6a3cf688de300298e7b3096e", 
        "name_en": "Chamkar Mon", 
        "name_km": "ចំការមន", 
        "sort_order": 2, 
        "is_active": True
    },
    {
        "province_id": "6a3cf688de300298e7b3096f", 
        "name_en": "Siem Reap Municipality", 
        "name_km": "ក្រុងសៀមរាប", 
        "sort_order": 1, 
        "is_active": True
    },
    {
        "province_id": "6a3ca266d8bd8140b4403fe0", 
        "name_en": "Preah Sihanouk Municipality", 
        "name_km": "ក្រុងព្រះសីហនុ", 
        "sort_order": 1, 
        "is_active": True
    },
    {
        "province_id": "6a3ca266d8bd8140b4403fe1", 
        "name_en": "Battambang Municipality", 
        "name_km": "ក្រុងបាត់ដំបង", 
        "sort_order": 1, 
        "is_active": True
    }
]

async def seed_districts():
    print("⏳ Checking and Creating Districts...")
    
    if not districts_data:
        return

    operations = []
    for item in districts_data:
        op = UpdateOne(
            # ប្រើទាំង name_en និង province_id ដើម្បីស្វែងរក ធានាថាមិនជាន់គ្នា
            {"name_en": item["name_en"], "province_id": item["province_id"]}, 
            {"$set": item},          
            upsert=True              
        )
        operations.append(op)
    
    result = await districts_collection.bulk_write(operations)
    
    print(f"✅ Districts -> Add New: {result.upserted_count} | Update: {result.modified_count}")