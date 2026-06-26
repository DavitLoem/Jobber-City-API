from src.core.mongo import provinces_collection

provinces_data = [
    {"name": "Phnom Penh", "name_kh": "ភ្នំពេញ", "is_active": True},
    {"name": "Siem Reap", "name_kh": "សៀមរាប", "is_active": True},
    {"name": "Sihanoukville", "name_kh": "ព្រះសីហនុ", "is_active": True},
    {"name": "Battambang", "name_kh": "បាត់ដំបង", "is_active": True}
]

async def seed_provinces():
    print("⏳ Creating Provinces...")
    await provinces_collection.delete_many({})
    await provinces_collection.insert_many(provinces_data)
    print("Created Provinces Successfully!")