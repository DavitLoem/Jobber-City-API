from fastapi import APIRouter
from src.domains.category.schema.category_schema import CategoryResponse
from src.domains.category.services.category_service import CategoryService

router = APIRouter(prefix="/api/category", tags=["Mobile - Category"])

@router.get("/", response_model=list[CategoryResponse])
async def get_active_categories():
    return await CategoryService.get_active_categories()