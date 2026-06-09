from typing import Optional, List
from src.core.mongo import categories_collection

# 📍 Mobile Category Service

async def get_active_categories(search: Optional[str] = None) -> List[dict]:
    """Mobile ទាញយកតែប្រភេទការងារដែលកំពុងបើកដំណើរការ (អាច Search បាន)"""
    
    # ១. បង្ខំលក្ខខណ្ឌ: ត្រូវតែមាន is_active = True ជានិច្ច
    query = {"is_active": True}

    # ២. បើមានការ Search តាមឈ្មោះ
    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    # ៣. ទាញយកទិន្នន័យពី DB រួចតម្រៀបតាម sort_order និង name
    cursor = categories_collection.find(query).sort([("sort_order", 1), ("name", 1)])
    categories = await cursor.to_list(length=1000)
    
    # ៤. រៀបចំទិន្នន័យ _id ទៅជា id
    for cat in categories:
        cat["id"] = str(cat.pop("_id"))
        
    return categories