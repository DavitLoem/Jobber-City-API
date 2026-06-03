from datetime import datetime, timezone
from fastapi import HTTPException
from bson import ObjectId
from src.core.mongo import provinces_collection, districts_collection
from src.domains.location.location_schema import ProvinceRequest, DistrictRequest
from src.domains.location.models.province_model import create_province_model

# ==========================================
# 📍 ផ្នែកខេត្ត/ក្រុង (PROVINCES CRUD)
# ==========================================

async def create_province(data: ProvinceRequest) -> dict:
    """បង្កើតខេត្តថ្មី"""
    # ១. ឆែកមើលក្រែងលោមានឈ្មោះខេត្តនេះរួចហើយ
    existing_province = await provinces_collection.find_one({
        "$or": [{"name_km": data.name_km}, {"name_en": data.name_en}]
    })
    if existing_province:
        raise HTTPException(status_code=400, detail="The province already exists")

    new_province = create_province_model(
        name_km=data.name_km,
        name_en=data.name_en,
        sort_order=data.sort_order,
        is_active=data.is_active
    )

    # ៣. Save ចូល Database
    result = await provinces_collection.insert_one(new_province)
    
    # ៤. រៀបចំទិន្នន័យដើម្បីបោះត្រឡប់ទៅឱ្យ API វិញ (ProvinceResponse)
    new_province["id"] = str(result.inserted_id)
    return new_province

async def get_all_provinces_admin() -> list[dict]:
    """ទាញយកខេត្តទាំងអស់សម្រាប់ Admin (ទាំង Active និង Inactive)"""
    # តម្រៀបតាម sort_order រួចតាមឈ្មោះ
    cursor = provinces_collection.find({}).sort([("sort_order", 1), ("name_en", 1)])
    provinces = await cursor.to_list(length=100)
    
    for prov in provinces:
        prov["id"] = str(prov.pop("_id"))
    return provinces

async def update_province(province_id: str, data: ProvinceRequest) -> dict:
    """កែប្រែទិន្នន័យខេត្ត"""
    if not ObjectId.is_valid(province_id):
        raise HTTPException(status_code=400, detail="លេខសម្គាល់ខេត្តមិនត្រឹមត្រូវទេ")

    update_data = data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc)

    result = await provinces_collection.find_one_and_update(
        {"_id": ObjectId(province_id)},
        {"$set": update_data},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="រកមិនឃើញខេត្តនេះទេ")

    result["id"] = str(result.pop("_id"))
    return result

async def delete_province(province_id: str) -> dict:
    """លុបខេត្ត (Soft Delete: គ្រាន់តែប្តូរ is_active=False)"""
    if not ObjectId.is_valid(province_id):
        raise HTTPException(status_code=400, detail="លេខសម្គាល់ខេត្តមិនត្រឹមត្រូវទេ")

    result = await provinces_collection.find_one_and_update(
        {"_id": ObjectId(province_id)},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="រកមិនឃើញខេត្តនេះទេ")

    result["id"] = str(result.pop("_id"))
    return result


# ==========================================
# 📍 ផ្នែកស្រុក/ខណ្ឌ (DISTRICTS CRUD)
# ==========================================

async def create_district(data: DistrictRequest) -> dict:
    """បង្កើតស្រុកថ្មី"""
    if not ObjectId.is_valid(data.province_id):
        raise HTTPException(status_code=400, detail="លេខសម្គាល់ខេត្ត (Province ID) មិនត្រឹមត្រូវទេ")

    # ១. ផ្ទៀងផ្ទាត់ថាតើខេត្តមេរបស់វាពិតជាមានមែនឬទេ
    parent_province = await provinces_collection.find_one({"_id": ObjectId(data.province_id)})
    if not parent_province:
        raise HTTPException(status_code=404, detail="រកមិនឃើញខេត្តមេសម្រាប់ស្រុកនេះទេ")

    # ២. ឆែកមើលក្រែងលោមានឈ្មោះស្រុកនេះស្ទួននៅក្នុងខេត្តដដែល
    existing_district = await districts_collection.find_one({
        "province_id": ObjectId(data.province_id),
        "$or": [{"name_km": data.name_km}, {"name_en": data.name_en}]
    })
    if existing_district:
        raise HTTPException(status_code=400, detail="ឈ្មោះស្រុកនេះមានរួចហើយនៅក្នុងខេត្តនេះ")

    new_district = data.model_dump()
    new_district["province_id"] = ObjectId(new_district["province_id"]) # បំប្លែងទៅ ObjectId មុន Save
    new_district["created_at"] = datetime.now(timezone.utc)
    new_district["updated_at"] = datetime.now(timezone.utc)

    result = await districts_collection.insert_one(new_district)
    
    new_district["id"] = str(result.inserted_id)
    new_district["province_id"] = str(new_district["province_id"])
    return new_district

async def get_districts_by_province_admin(province_id: str) -> list[dict]:
    """ទាញយកស្រុកទាំងអស់នៅក្នុងខេត្តណាមួយ"""
    if not ObjectId.is_valid(province_id):
        raise HTTPException(status_code=400, detail="លេខសម្គាល់ខេត្តមិនត្រឹមត្រូវទេ")

    cursor = districts_collection.find({"province_id": ObjectId(province_id)}).sort([("sort_order", 1), ("name_en", 1)])
    districts = await cursor.to_list(length=200) # ស្រុកក្នុងមួយខេត្តប្រហែលមិនលើស ២០០ ទេ
    
    for dist in districts:
        dist["id"] = str(dist.pop("_id"))
        dist["province_id"] = str(dist["province_id"])
    return districts

async def update_district(district_id: str, data: DistrictRequest) -> dict:
    """កែប្រែទិន្នន័យស្រុក"""
    if not ObjectId.is_valid(district_id) or not ObjectId.is_valid(data.province_id):
        raise HTTPException(status_code=400, detail="លេខសម្គាល់មិនត្រឹមត្រូវទេ")

    update_data = data.model_dump()
    update_data["province_id"] = ObjectId(update_data["province_id"])
    update_data["updated_at"] = datetime.now(timezone.utc)

    result = await districts_collection.find_one_and_update(
        {"_id": ObjectId(district_id)},
        {"$set": update_data},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="រកមិនឃើញស្រុកនេះទេ")

    result["id"] = str(result.pop("_id"))
    result["province_id"] = str(result["province_id"])
    return result

async def delete_district(district_id: str) -> dict:
    """លុបស្រុក (Soft Delete)"""
    if not ObjectId.is_valid(district_id):
        raise HTTPException(status_code=400, detail="លេខសម្គាល់ស្រុកមិនត្រឹមត្រូវទេ")

    result = await districts_collection.find_one_and_update(
        {"_id": ObjectId(district_id)},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="រកមិនឃើញស្រុកនេះទេ")

    result["id"] = str(result.pop("_id"))
    result["province_id"] = str(result["province_id"])
    return result