from datetime import datetime, timezone
from fastapi import HTTPException
from bson import ObjectId
from src.core.mongo import provinces_collection, districts_collection
from src.domains.location.location_schema import ProvinceRequest, DistrictRequest
from src.domains.location.models.province_model import ProvinceModel
from src.domains.location.models.district_model import DistrictModel

# ==========================================
# 📍 ផ្នែកខេត្ត/ក្រុង (PROVINCES CRUD)
# ==========================================

async def create_province(data: ProvinceRequest) -> dict:
    """បង្កើតខេត្តថ្មី"""
    
    # ១. រៀបចំលក្ខខណ្ឌឆែកស្ទួនយ៉ាងឆ្លាតវៃ (បញ្ចៀសការឆែកតម្លៃ null)
    or_conditions = [{"name_en": data.name_en}]
    if data.name_km: # ថែមលក្ខខណ្ឌ name_km លុះត្រាតែមានទិន្នន័យ (មិនមែន None)
        or_conditions.append({"name_km": data.name_km})

    existing_province = await provinces_collection.find_one({
        "$or": or_conditions
    })
    
    if existing_province:
        if data.name_km and existing_province.get("name_km") == data.name_km and existing_province.get("name_en") == data.name_en:
            error_msg = f"A province with the same Khmer and English names already exists."
        elif data.name_km and existing_province.get("name_km") == data.name_km:
            error_msg = f"A province with the same Khmer name already exists."
        else:
            error_msg = f"A province with the same English name already exists."

        raise HTTPException(status_code=400, detail=error_msg)

    # ២. ប្រើ Model ដើម្បីចាត់ចែងទិន្នន័យ
    new_province = ProvinceModel(
        name_km=data.name_km,
        name_en=data.name_en,
        sort_order=data.sort_order,
        is_active=data.is_active
    ).to_create_dict()

    # ៣. Save ចូល Database
    result = await provinces_collection.insert_one(new_province)
    
    # ៤. រៀបចំទិន្នន័យដើម្បីបោះត្រឡប់ទៅឱ្យ API វិញ
    new_province["id"] = str(result.inserted_id)
    return new_province

async def get_all_provinces_admin() -> list[dict]:
    """ទាញយកខេត្តទាំងអស់សម្រាប់ Admin (ទាំង Active និង Inactive)"""
    cursor = provinces_collection.find({}).sort([("sort_order", 1), ("name_en", 1)])
    provinces = await cursor.to_list(length=100)
    
    for prov in provinces:
        prov["id"] = str(prov.pop("_id"))
    return provinces

async def update_province(province_id: str, data: ProvinceRequest) -> dict:
    """កែប្រែទិន្នន័យខេត្ត"""
    if not ObjectId.is_valid(province_id):
        raise HTTPException(status_code=400, detail="Invalid province ID")

    update_data = ProvinceModel(
        name_km=data.name_km,
        name_en=data.name_en,
        sort_order=data.sort_order,
        is_active=data.is_active
    ).to_update_dict()

    result = await provinces_collection.find_one_and_update(
        {"_id": ObjectId(province_id)},
        {"$set": update_data},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="The province not found")

    result["id"] = str(result.pop("_id"))
    return result

async def delete_province(province_id: str) -> dict:
    """លុបខេត្ត (Soft Delete) ដោយប្រើ Model"""
    if not ObjectId.is_valid(province_id):
        raise HTTPException(status_code=400, detail="Invalid province ID")

    update_data = ProvinceModel.to_delete_dict()

    result = await provinces_collection.find_one_and_update(
        {"_id": ObjectId(province_id)},
        {"$set": update_data},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="The province not found")

    result["id"] = str(result.pop("_id"))
    return result


# ==========================================
# 📍 ផ្នែកស្រុក/ខណ្ឌ (DISTRICTS CRUD)
# ==========================================

async def create_district(data: DistrictRequest) -> dict:
    """បង្កើតស្រុកថ្មី ដោយប្រើ Model"""
    if not ObjectId.is_valid(data.province_id):
        raise HTTPException(status_code=400, detail="Invalid province ID")

    parent_province = await provinces_collection.find_one({"_id": ObjectId(data.province_id)})
    if not parent_province:
        raise HTTPException(status_code=404, detail="The province not found")

    # 🎯 រៀបចំលក្ខខណ្ឌឆែកស្ទួនសម្រាប់ស្រុក ដូចដែលបានធ្វើលើខេត្តដែរ
    or_conditions = [{"name_en": data.name_en}]
    if data.name_km:
        or_conditions.append({"name_km": data.name_km})

    existing_district = await districts_collection.find_one({
        "province_id": ObjectId(data.province_id),
        "$or": or_conditions
    })
    
    if existing_district:
        if data.name_km and existing_district.get("name_km") == data.name_km and existing_district.get("name_en") == data.name_en:
            error_msg = f"A district with the same Khmer and English names already exists in this province."
        elif data.name_km and existing_district.get("name_km") == data.name_km:
            error_msg = f"A district with the same Khmer name already exists in this province."
        else:
            error_msg = f"A district with the same English name already exists in this province."
        raise HTTPException(status_code=400, detail=error_msg)

    new_district = DistrictModel(
        province_id=data.province_id,
        name_km=data.name_km,
        name_en=data.name_en,
        sort_order=data.sort_order,
        is_active=data.is_active
    ).to_create_dict()

    result = await districts_collection.insert_one(new_district)
    
    new_district["id"] = str(result.inserted_id)
    new_district["province_id"] = str(new_district["province_id"])
    return new_district

async def get_districts_by_province_admin(province_id: str) -> list[dict]:
    """ទាញយកស្រុកទាំងអស់នៅក្នុងខេត្តណាមួយ"""
    if not ObjectId.is_valid(province_id):
        raise HTTPException(status_code=400, detail="Invalid province ID")

    cursor = districts_collection.find({"province_id": ObjectId(province_id)}).sort([("sort_order", 1), ("name_en", 1)])
    districts = await cursor.to_list(length=200)
    
    for dist in districts:
        dist["id"] = str(dist.pop("_id"))
        dist["province_id"] = str(dist["province_id"])
    return districts

async def update_district(district_id: str, data: DistrictRequest) -> dict:
    """កែប្រែទិន្នន័យស្រុក ដោយប្រើ Model"""
    if not ObjectId.is_valid(district_id) or not ObjectId.is_valid(data.province_id):
        raise HTTPException(status_code=400, detail="Invalid district ID or province ID")

    update_data = DistrictModel(
        province_id=data.province_id,
        name_km=data.name_km,
        name_en=data.name_en,
        sort_order=data.sort_order,
        is_active=data.is_active
    ).to_update_dict()
    
    result = await districts_collection.find_one_and_update(
        {"_id": ObjectId(district_id)},
        {"$set": update_data},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="The district not found")

    result["id"] = str(result.pop("_id"))
    result["province_id"] = str(result["province_id"])
    return result

async def delete_district(district_id: str) -> dict:
    """លុបស្រុក (Soft Delete) ដោយប្រើ Model"""
    if not ObjectId.is_valid(district_id):
        raise HTTPException(status_code=400, detail="Invalid district ID")

    update_data = DistrictModel.to_delete_dict()

    result = await districts_collection.find_one_and_update(
        {"_id": ObjectId(district_id)},
        {"$set": update_data},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="The district not found")

    result["id"] = str(result.pop("_id"))
    result["province_id"] = str(result["province_id"])
    return result