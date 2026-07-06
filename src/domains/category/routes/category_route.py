from fastapi import APIRouter, Query, Depends
from typing import List, Optional

from src.core.response import APIResponse
from src.domains.category.schema.category_schema import CategoryResponse
import src.domains.category.services.category_service as mobile_service

from src.dependencies.dependencies import require_mobile_users

router = APIRouter(
    prefix="/api/categories",
    tags=["Mobile - Categories"],
    dependencies=[Depends(require_mobile_users)]
)

@router.get("/", response_model=APIResponse[List[CategoryResponse]])
async def get_mobile_categories_route(
    search: Optional[str] = Query(None, description="ស្វែងរកតាមឈ្មោះប្រភេទការងារ")
):
    """App ទាញយកបញ្ជីប្រភេទការងារ (សម្រាប់ Dropdown ពេល Post ការងារ ឬ Filter)"""
    
    result = await mobile_service.get_active_categories(search=search)
    return APIResponse(
        success=True,
        message="ទាញយកបញ្ជីប្រភេទការងារជោគជ័យ",
        data=result
    )