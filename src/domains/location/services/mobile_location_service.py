from typing import Optional
from fastapi import HTTPException
from bson import ObjectId
from src.core.mongo import provinces_collection, districts_collection

async def get_active_provinces(search: Optional[str] = None) -> list[dict]:
    """Mobile ទាញយកតែខេត្តដែលកំពុងបើកដំណើរការ (អាច Search បាន)"""
    
    # 🎯 ១. បង្ខំលក្ខខណ្ឌ: ត្រូវតែមាន is_active = True ជានិច្ច
    query = {"is_active": True}

    # 🎯 ២. បើមានការ Search ថែមលក្ខខណ្ឌ $or
    if search:
        query["$or"] = [
            {"name_km": {"$regex": search, "$options": "i"}},
            {"name_en": {"$regex": search, "$options": "i"}}
        ]

    cursor = provinces_collection.find(query).sort([("sort_order", 1), ("name_en", 1)])
    provinces = await cursor.to_list(length=100)
    
    for prov in provinces:
        prov["id"] = str(prov.pop("_id"))
    return provinces

async def get_active_districts_by_province(province_id: str, search: Optional[str] = None) -> list[dict]:
    """Mobile ទាញយកស្រុកក្នុងខេត្តណាមួយ ដែលកំពុងបើកដំណើរការ (អាច Search បាន)"""
    if not ObjectId.is_valid(province_id):
        raise HTTPException(status_code=400, detail="Invalid province ID")

    # 🎯 ១. បង្ខំលក្ខខណ្ឌ: ត្រូវតែមាន province_id ត្រឹមត្រូវ និង is_active = True ជានិច្ច
    query = {
        "province_id": ObjectId(province_id),
        "is_active": True
    }

    # 🎯 ២. បើមានការ Search
    if search:
        query["$or"] = [
            {"name_km": {"$regex": search, "$options": "i"}},
            {"name_en": {"$regex": search, "$options": "i"}}
        ]

    cursor = districts_collection.find(query).sort([("sort_order", 1), ("name_en", 1)])
    
    districts = await cursor.to_list(length=200)
    
    for dist in districts:
        dist["id"] = str(dist.pop("_id"))
        dist["province_id"] = str(dist["province_id"])
    return districts