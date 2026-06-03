from bson import ObjectId
from datetime import datetime
# Import categories_collection ពី mongo.py ផ្ទាល់
from src.core.mongo import categories_collection 
from src.domains.category.model.category_model import CategoryModel
from src.domains.category.schema.category_schema import CategoryRequest

def helper_format_category(cat: dict) -> dict:
    if cat:
        cat["id"] = str(cat.pop("_id"))
    return cat

class AdminCategoryService:
    @staticmethod
    async def create(data: CategoryRequest) -> dict:
        new_cat = CategoryModel(
            name=data.name,
            icon_url=data.icon_url,
            sort_order=data.sort_order if data.sort_order is not None else 99
        )
        # ប្រសិនបើចង់កំណត់ស្ថានភាព is_active ទៅតាម payload បន្ថែម៖
        new_cat["is_active"] = data.is_active if data.is_active is not None else True
        
        await categories_collection.insert_one(new_cat)
        return helper_format_category(new_cat)

    @staticmethod
    async def get_all() -> list:
        cats = []
        cursor = categories_collection.find().sort("sort_order", 1)
        async for c in cursor:
            cats.append(helper_format_category(c))
        return cats

    @staticmethod
    async def update(cat_id: str, data: CategoryRequest) -> dict:
        if not ObjectId.is_valid(cat_id):
            return None
            
        # យកតែ Field ណាដែលមានការបញ្ជូនមកផ្លាស់ប្តូរ (មិនមែន None)
        update_dict = {k: v for k, v in data.dict().items() if v is not None}
        if not update_dict:
            return None
            
        update_dict["updated_at"] = datetime.now()
        
        updated_cat = await categories_collection.find_one_and_update(
            {"_id": ObjectId(cat_id)},
            {"$set": update_dict},
            return_document=True
        )
        return helper_format_category(updated_cat)

    @staticmethod
    async def delete(cat_id: str) -> bool:
        if not ObjectId.is_valid(cat_id):
            return False
        res = await categories_collection.delete_one({"_id": ObjectId(cat_id)})
        return res.deleted_count > 0