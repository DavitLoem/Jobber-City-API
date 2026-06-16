from bson import ObjectId
from fastapi import HTTPException
from typing import List

from src.core.mongo import categories_collection 
from src.domains.category.model.category_model import CategoryModel # បញ្ជាក់ផ្លូវ Import ឱ្យត្រូវ
from src.domains.category.schema.category_schema import CategoryRequest

# ==========================================
# 📍 Admin Category Services
# ==========================================

async def create_category(data: CategoryRequest) -> dict:
    """បង្កើតប្រភេទការងារថ្មី (Admin)"""
    
    # ១. ឆែកឈ្មោះស្ទួន
    existing_cat = await categories_collection.find_one({
        "name": {"$regex": f"^{data.name}$", "$options": "i"} # ស្វែងរកដោយមិនប្រកាន់អក្សរធំតូច
    })
    if existing_cat:
        raise HTTPException(status_code=400, detail=f"Just one category with the name '{data.name}' already exists.")

    # ២. ប្រើ Model ដើម្បីចាត់ចែងទិន្នន័យ
    new_cat_data = CategoryModel(
        name=data.name,
        icon_url=data.icon_url,
        sort_order=data.sort_order,
        is_active=data.is_active
    ).to_create_dict()

    # ៣. Save ចូល Database
    result = await categories_collection.insert_one(new_cat_data)
    
    # ៤. រៀបចំទិន្នន័យត្រឡប់ទៅវិញ
    new_cat_data["id"] = str(result.inserted_id)
    new_cat_data.pop("_id", None)
    return new_cat_data

from typing import Optional, List

async def get_all_categories_admin(search: Optional[str] = None, is_active: Optional[bool] = None) -> List[dict]:
    """ទាញយកប្រភេទការងារទាំងអស់សម្រាប់ Admin (មានមុខងារ Search និង Filter)"""
    
    query = {}

    # ១. បើមានការ Filter តាម Status
    if is_active is not None:
        query["is_active"] = is_active

    # ២. បើមានការ Search តាមឈ្មោះ
    if search:
        query["name"] = {"$regex": search, "$options": "i"} # i = អត់ប្រកាន់អក្សរធំតូច

    cursor = categories_collection.find(query).sort([("sort_order", 1), ("name", 1)])
    
    # យើងអាចដំឡើងដល់ 1000 ដើម្បីឱ្យប្រាកដថាទាញមកអស់ ព្រោះ Category មិនច្រើនដូច User ទេ
    categories = await cursor.to_list(length=1000) 
    
    for cat in categories:
        cat["id"] = str(cat.pop("_id"))
    return categories

async def update_category(cat_id: str, data: CategoryRequest) -> dict:
    """កែប្រែទិន្នន័យប្រភេទការងារ"""
    
    if not ObjectId.is_valid(cat_id):
        raise HTTPException(status_code=400, detail="ID is not valid")

    # ១. ឆែកឈ្មោះស្ទួន ករណីគាត់ប្តូរឈ្មោះជាន់គេ
    existing_cat = await categories_collection.find_one({
        "name": {"$regex": f"^{data.name}$", "$options": "i"},
        "_id": {"$ne": ObjectId(cat_id)} # លើកលែង ID ខ្លួនឯង
    })
    if existing_cat:
        raise HTTPException(status_code=400, detail=f"Category with the name '{data.name}' already exists.")

    # ២. ប្រើ Model ដើម្បី Update (វានឹង Update ម៉ោង updated_at ឱ្យដោយស្វ័យប្រវត្តិ)
    update_data = CategoryModel(
        name=data.name,
        icon_url=data.icon_url,
        sort_order=data.sort_order,
        is_active=data.is_active
    ).to_update_dict()

    result = await categories_collection.find_one_and_update(
        {"_id": ObjectId(cat_id)},
        {"$set": update_data},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="Category not found")

    result["id"] = str(result.pop("_id"))
    return result

async def delete_category(cat_id: str) -> dict:
    """លុបប្រភេទការងារ (Soft Delete: ដូរ is_active ទៅ False)"""
    
    if not ObjectId.is_valid(cat_id):
        raise HTTPException(status_code=400, detail="ID is not valid")

    # ប្រើ Model ដើម្បីទាញយកទម្រង់ Soft Delete
    update_data = CategoryModel.to_delete_dict()

    result = await categories_collection.find_one_and_update(
        {"_id": ObjectId(cat_id)},
        {"$set": update_data},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="Category not found")

    result["id"] = str(result.pop("_id"))
    return result