from pymongo import UpdateOne

from src.core.mongo import industries_collection

industries_data = [
    {"name": "Information Technology", "description": "IT, Software, and Hardware", "is_active": True},
    {"name": "Banking & Finance", "description": "Banks, Microfinance, and Insurance", "is_active": True},
    {"name": "Education", "description": "Schools, Universities, and Training", "is_active": True},
    {"name": "Real Estate", "description": "Property Management and Sales", "is_active": True},
    {"name": "Hospitality & Tourism", "description": "Hotels, Restaurants, and Travel", "is_active": True}
]

async def seed_industries():
    print("⏳ Checking and Creating Industries...")
    
    # ប្រសិនបើបញ្ជីទិន្នន័យទទេ មិនបាច់ធ្វើអ្វីទេ
    if not industries_data:
        return

    # បង្កើតប្រតិបត្តិការ (Operations) សម្រាប់រាល់ទិន្នន័យនីមួយៗ
    operations = []
    for item in industries_data:
        op = UpdateOne(
            {"name": item["name"]},  # ១. លក្ខខណ្ឌស្វែងរក៖ ឆែកមើលថាតើមានឈ្មោះនេះក្នុង DB ឬនៅ?
            {"$set": item},          # ២. បើរកឃើញ (មានន័យថាដដែល): វាគ្រាន់តែ Update ក្រែងលោអ្នកកែអក្ខរាវិរុទ្ធ
            upsert=True              # ៣. 🎯 បើរកមិនឃើញ (មានន័យថាទិន្នន័យថ្មី): វានឹង Add ថ្មីចូលទៅក្នុង DB តែម្តង!
        )
        operations.append(op)
    
    # បញ្ជាឱ្យ MongoDB ធ្វើការងារទាំងអស់នេះក្នុងពេលតែមួយ (លឿន និងមានសុវត្ថិភាព)
    result = await industries_collection.bulk_write(operations)
    
    print(f"✅ Industries -> Add New: {result.upserted_count} | Update: {result.modified_count}")