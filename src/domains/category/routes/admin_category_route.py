from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional

from src.dependencies.dependencies import require_admin 
from src.core.response import APIResponse

from src.domains.category.schema.category_schema import CategoryResponse, CategoryRequest
import src.domains.category.services.admin_category_service as admin_service

router = APIRouter(
    prefix="/api/admin/categories",
    tags=["Admin - Categories"],
    dependencies=[Depends(require_admin)]
)

@router.post("/", response_model=APIResponse[CategoryResponse], status_code=status.HTTP_201_CREATED)
async def create_category_route(payload: CategoryRequest):
    """Admin បង្កើតប្រភេទការងារថ្មី"""
    result = await admin_service.create_category(payload)
    return APIResponse(
        success=True,
        message="Job category created successfully",
        data=result
    )

@router.get("/", response_model=APIResponse[List[CategoryResponse]])
async def get_categories_route(
    # 🎯 ៤. បន្ថែមមុខងារ Search និង Filter
    search: Optional[str] = Query(None, description="ស្វែងរកតាមឈ្មោះប្រភេទការងារ"),
    is_active: Optional[bool] = Query(None, description="ចម្រោះយកតែ Active ឬ Inactive")
):
    """Admin ទាញយកបញ្ជីប្រភេទការងារទាំងអស់"""
    result = await admin_service.get_all_categories_admin(search=search, is_active=is_active)
    return APIResponse(
        success=True,
        message="Job categories retrieved successfully",
        data=result
    )

@router.put("/{category_id}", response_model=APIResponse[CategoryResponse])
async def update_category_route(category_id: str, payload: CategoryRequest):
    """Admin កែប្រែទិន្នន័យប្រភេទការងារ"""
    # មិនបាច់សរសេរ Error ទេ ព្រោះ Service ជាអ្នកបោះ HTTPException បើមានបញ្ហា
    updated = await admin_service.update_category(category_id, payload)
    return APIResponse(
        success=True,
        message="Job category updated successfully",
        data=updated
    )

@router.delete("/{category_id}", response_model=APIResponse[None])
async def delete_category_route(category_id: str):
    """Admin លុបប្រភេទការងារ (Soft Delete)"""
    await admin_service.delete_category(category_id)
    return APIResponse(
        success=True,
        message="Job category deleted successfully",
        data=None
    )