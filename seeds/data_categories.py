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
    },
    {
        "name": "Human Resources", 
        "icon_url": "https://example.com/icons/hr.png", 
        "sort_order": 5, 
        "is_active": True
    },
    {
        "name": "Customer Support", 
        "icon_url": "https://example.com/icons/support.png", 
        "sort_order": 6, 
        "is_active": True
    },
    {
        "name": "Engineering & Architecture", 
        "icon_url": "https://example.com/icons/engineering.png", 
        "sort_order": 7, 
        "is_active": True
    },
    {
        "name": "Legal", 
        "icon_url": "https://example.com/icons/legal.png", 
        "sort_order": 8, 
        "is_active": True
    },
    {
        "name": "Healthcare & Medical", 
        "icon_url": "https://example.com/icons/healthcare.png", 
        "sort_order": 9, 
        "is_active": True
    },
    {
        "name": "Education & Training", 
        "icon_url": "https://example.com/icons/education.png", 
        "sort_order": 10, 
        "is_active": True
    }
]

async def seed_categories():
    print("⏳ Checking and Creating Categories...")
    
    # ប្រសិនបើបញ្ជីទិន្នន័យទទេ មិនបាច់ធ្វើអ្វីទេ[cite: 1]
    if not categories_data:
        return

    # យោបល់កែលម្អ: បង្កើត Unique Index ដើម្បីការពារការបញ្ចូលឈ្មោះជាន់គ្នា និងជួយឱ្យការ Upsert កាន់តែលឿន
    await categories_collection.create_index("name", unique=True)

    # កំណត់ម៉ោងបច្ចុប្បន្ន[cite: 1]
    now = datetime.now(timezone.utc)
    
    # បង្កើតប្រតិបត្តិការ (Operations) សម្រាប់រាល់ទិន្នន័យនីមួយៗ[cite: 1]
    operations = []
    for item in categories_data:
        op = UpdateOne(
            {"name": item["name"]},
            {
                "$set": {
                    **item,
                    "updated_at": now # Update ម៉ោងជានិច្ចនៅពេលរត់ Seed ម្តងៗ[cite: 1]
                },
                "$setOnInsert": {
                    "created_at": now # បង្កើតម៉ោង created_at តែពេល Insert លើកដំបូងប៉ុណ្ណោះ[cite: 1]
                }
            },          
            upsert=True              
        )
        operations.append(op)
    
    # បញ្ជាឱ្យ MongoDB ធ្វើការងារទាំងអស់នេះក្នុងពេលតែមួយ[cite: 1]
    result = await categories_collection.bulk_write(operations)
    
    # បានកែឈ្មោះពី Industries មក Categories ឱ្យត្រូវនឹងទិន្នន័យជាក់ស្តែង[cite: 1]
    print(f"✅ Categories -> Add New: {result.upserted_count} | Update: {result.modified_count}")