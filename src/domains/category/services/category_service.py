from src.core.mongo import categories_collection
from src.domains.category.services.admin_category_service import helper_format_category

class CategoryService:
    @staticmethod
    async def get_active_categories() -> list:
        cats = []
        cursor = categories_collection.find({"is_active": True}).sort("sort_order", 1)
        async for c in cursor:
            cats.append(helper_format_category(c))
        return cats