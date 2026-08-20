from pymongo import UpdateOne
from datetime import datetime, timezone
from src.core.mongo import provinces_collection

provinces_data = [
    {"name_en": "Phnom Penh", "name_kh": "ភ្នំពេញ", "is_active": True},
    {"name_en": "Banteay Meanchey", "name_kh": "បន្ទាយមានជ័យ", "is_active": True},
    {"name_en": "Battambang", "name_kh": "បាត់ដំបង", "is_active": True},
    {"name_en": "Kampong Cham", "name_kh": "កំពង់ចាម", "is_active": True},
    {"name_en": "Kampong Chhnang", "name_kh": "កំពង់ឆ្នាំង", "is_active": True},
    {"name_en": "Kampong Speu", "name_kh": "កំពង់ស្ពឺ", "is_active": True},
    {"name_en": "Kampong Thom", "name_kh": "កំពង់ធំ", "is_active": True},
    {"name_en": "Kampot", "name_kh": "កំពត", "is_active": True},
    {"name_en": "Kandal", "name_kh": "កណ្តាល", "is_active": True},
    {"name_en": "Kep", "name_kh": "កែប", "is_active": True},
    {"name_en": "Koh Kong", "name_kh": "កោះកុង", "is_active": True},
    {"name_en": "Kratie", "name_kh": "ក្រចេះ", "is_active": True},
    {"name_en": "Mondulkiri", "name_kh": "មណ្ឌលគិរី", "is_active": True},
    {"name_en": "Oddar Meanchey", "name_kh": "ឧត្តរមានជ័យ", "is_active": True},
    {"name_en": "Pailin", "name_kh": "ប៉ៃលិន", "is_active": True},
    {"name_en": "Preah Sihanouk", "name_kh": "ព្រះសីហនុ", "is_active": True}, 
    {"name_en": "Preah Vihear", "name_kh": "ព្រះវិហារ", "is_active": True},
    {"name_en": "Prey Veng", "name_kh": "ព្រៃវែង", "is_active": True},
    {"name_en": "Pursat", "name_kh": "ពោធិ៍សាត់", "is_active": True},
    {"name_en": "Ratanakiri", "name_kh": "រតនគិរី", "is_active": True},
    {"name_en": "Siem Reap", "name_kh": "សៀមរាប", "is_active": True},
    {"name_en": "Stung Treng", "name_kh": "ស្ទឹងត្រែង", "is_active": True},
    {"name_en": "Svay Rieng", "name_kh": "ស្វាយរៀង", "is_active": True},
    {"name_en": "Takeo", "name_kh": "តាកែវ", "is_active": True},
    {"name_en": "Tboung Khmum", "name_kh": "ត្បូងឃ្មុំ", "is_active": True}
]

async def seed_provinces():
    print("⏳ Checking and Creating Provinces...")
    
    if not provinces_data: #[cite: 4]
        return

    # បង្កើត Unique Index លើ name_en[cite: 4]
    await provinces_collection.create_index("name_en", unique=True)

    now = datetime.now(timezone.utc) #[cite: 4]
    operations = []
    
    # ប្រើ enumerate ដើម្បីយក index ចាប់ពីលេខ 1 ទៅដល់ 25
    for index, item in enumerate(provinces_data, start=1):
        
        # បញ្ចូល sort_order ដោយស្វ័យប្រវត្តិតាមលំដាប់ (index) នៃបញ្ជីទិន្នន័យ
        item["sort_order"] = index 
        
        op = UpdateOne(
            {"name_en": item["name_en"]}, #[cite: 4]
            {
                "$set": {
                    **item,
                    "updated_at": now #[cite: 4]
                },
                "$setOnInsert": {
                    "created_at": now #[cite: 4]
                }
            },          
            upsert=True #[cite: 4]             
        )
        operations.append(op)
    
    result = await provinces_collection.bulk_write(operations) #[cite: 4]
    
    print(f"✅ Provinces -> Add New: {result.upserted_count} | Update: {result.modified_count}") #[cite: 4]