from pymongo import UpdateOne
from bson import ObjectId
from datetime import datetime, timezone
from src.core.mongo import districts_collection

# កំណត់ Object ID របស់ភ្នំពេញជាអថេរមួយដើម្បីងាយស្រួលប្រើប្រាស់
PHNOM_PENH_ID = ObjectId("6a6d5722f7698b4ac44385d6")

districts_data = [
    {"province_id": PHNOM_PENH_ID, "name_en": "Chamkar Mon", "name_km": "ចំការមន", "sort_order": 1, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Daun Penh", "name_km": "ដូនពេញ", "sort_order": 2, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Prampir Makara", "name_km": "៧មករា", "sort_order": 3, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Tuol Kouk", "name_km": "ទួលគោក", "sort_order": 4, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Dangkao", "name_km": "ដង្កោ", "sort_order": 5, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Mean Chey", "name_km": "មានជ័យ", "sort_order": 6, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Russey Keo", "name_km": "ឫស្សីកែវ", "sort_order": 7, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Sen Sok", "name_km": "សែនសុខ", "sort_order": 8, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Pou Senchey", "name_km": "ពោធិ៍សែនជ័យ", "sort_order": 9, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Chroy Changvar", "name_km": "ជ្រោយចង្វារ", "sort_order": 10, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Prek Pnov", "name_km": "ព្រែកព្នៅ", "sort_order": 11, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Chbar Ampov", "name_km": "ច្បារអំពៅ", "sort_order": 12, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Boeng Keng Kang", "name_km": "បឹងកេងកង", "sort_order": 13, "is_active": True},
    {"province_id": PHNOM_PENH_ID, "name_en": "Kamboul", "name_km": "កំបូល", "sort_order": 14, "is_active": True}
]

async def seed_districts():
    print("⏳ Checking and Creating Districts...")
    
    if not districts_data:
        return

    # បង្កើត Compound Index ដើម្បីឱ្យការទាញទិន្នន័យខណ្ឌតាមខេត្តនីមួយៗកាន់តែលឿន
    await districts_collection.create_index([("province_id", 1), ("name_en", 1)], unique=True)

    now = datetime.now(timezone.utc)
    operations = []
    
    for item in districts_data:
        op = UpdateOne(
            # ប្រើទាំង name_en និង province_id ដើម្បីស្វែងរក ធានាថាមិនជាន់គ្នា[cite: 3]
            {"name_en": item["name_en"], "province_id": item["province_id"]}, 
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
    
    result = await districts_collection.bulk_write(operations)
    
    print(f"✅ Districts -> Add New: {result.upserted_count} | Update: {result.modified_count}")