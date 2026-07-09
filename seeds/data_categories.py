from pymongo import UpdateOne
from datetime import datetime, timezone
from src.core.mongo import categories_collection

categories_data = [
    {
        "name": "IT & Software", 
        "icon_url": "https://example.com/icons/it.png", 
        "sort_order": 1, 
        "is_active": True
    },
    {
        "name": "Marketing & Sales", 
        "icon_url": "https://example.com/icons/marketing.png", 
        "sort_order": 2, 
        "is_active": True
    },
    {
        "name": "Accounting & Finance", 
        "icon_url": "https://example.com/icons/finance.png", 
        "sort_order": 3, 
        "is_active": True
    },
    {
        "name": "Design & Creative", 
        "icon_url": "https://example.com/icons/design.png", 
        "sort_order": 4, 
        "is_active": True
    }
]

async def seed_categories():
    print("⏳ Checking and Creating Categories...")
    
    # ប្រសិនបើបញ្ជីទិន្នន័យទទេ មិនបាច់ធ្វើអ្វីទេ
    if not categories_data:
        return

    # កំណត់ម៉ោងបច្ចុប្បន្ន
    now = datetime.now(timezone.utc)
    
    # បង្កើតប្រតិបត្តិការ (Operations) សម្រាប់រាល់ទិន្នន័យនីមួយៗ
    operations = []
    for item in categories_data:
        op = UpdateOne(
            {"name": item["name"]},
            {
                "$set": {
                    **item,
                    "updated_at": now # Update ម៉ោងជានិច្ចនៅពេលរត់ Seed ម្តងៗ
                },
                "$setOnInsert": {
                    "created_at": now # បង្កើតម៉ោង created_at តែពេល Insert លើកដំបូងប៉ុណ្ណោះ
                }
            },          
            upsert=True              
        )
        operations.append(op)
    
    # បញ្ជាឱ្យ MongoDB ធ្វើការងារទាំងអស់នេះក្នុងពេលតែមួយ
    result = await categories_collection.bulk_write(operations)
    
    # បានកែឈ្មោះពី Industries មក Categories ឱ្យត្រូវនឹងទិន្នន័យជាក់ស្តែង
    print(f"✅ Categories -> Add New: {result.upserted_count} | Update: {result.modified_count}")