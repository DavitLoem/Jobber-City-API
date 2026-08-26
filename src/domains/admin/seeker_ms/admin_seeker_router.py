from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from typing import Optional

from src.dependencies.dependencies import require_admin
from src.core.response import APIResponse

# នាំចូល Schemas 
from src.domains.admin.seeker_ms.admin_seeker_schema import (
    SeekerKpiResponse, 
    AdminSeekerListResponse
)

# នាំចូល Service
from src.domains.admin.seeker_ms.admin_seeker_service import AdminSeekerService

router = APIRouter(
    prefix="/api/admin/seekers",
    tags=["Admin - Job Seekers Management"],
    dependencies=[Depends(require_admin)] # 🔒 ការពារដោយទាមទារសិទ្ធិ Admin
)

seeker_service = AdminSeekerService()

# 🟢 ១. Route សម្រាប់ KPI Cards
@router.get("/kpis", response_model=APIResponse[SeekerKpiResponse])
async def get_seeker_kpis_route():
    """Admin ទាញយកទិន្នន័យ KPI Cards ទាំង ៤ (Total, Active, Suspended, Banned)"""
    result = await seeker_service.get_seeker_kpis()
    return APIResponse(
        success=True,
        message="Seeker KPIs retrieved successfully",
        data=result
    )

# 🟢 ២. Route សម្រាប់តារាងបញ្ជីអ្នកស្វែងរកការងារ
@router.get("/", response_model=APIResponse[AdminSeekerListResponse])
async def get_seeker_list_route(
    search: Optional[str] = Query(None, description="ស្វែងរកតាមឈ្មោះ ឬអ៊ីមែល"),
    status_filter: Optional[str] = Query(None, description="ចម្រោះយកតាម (active, suspended, banned)"),
    page: int = Query(1, ge=1, description="ទំព័រទីប៉ុន្មាន"),
    limit: int = Query(10, ge=1, le=100, description="ចំនួនទិន្នន័យក្នុងមួយទំព័រ")
):
    """Admin ទាញយកបញ្ជី Job Seekers គួបផ្សំជាមួយការ Search និង Filter តាម Status"""
    result = await seeker_service.get_seeker_list(
        search=search, 
        status_filter=status_filter, 
        page=page, 
        limit=limit
    )
    return APIResponse(
        success=True,
        message="Job Seekers list retrieved successfully",
        data=result
    )

# 🟢 ៣. Route សម្រាប់ប៊ូតុង Suspend, Ban, ឬ Activate លើ UI
@router.patch("/{user_id}/status", response_model=APIResponse)
async def update_seeker_status_route(
    user_id: str = Path(..., description="Object ID របស់ Seeker"),
    action: str = Query(..., description="សកម្មភាព (ត្រូវវាយ: activate, suspend, ឬ ban)")
):
    """Admin ផ្លាស់ប្តូរស្ថានភាពគណនីរបស់អ្នកស្វែងរកការងារ"""
    
    # Validation ការពារការវាយ Action ខុស
    valid_actions = ["activate", "suspend", "ban"]
    if action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Action must be one of {valid_actions}"
        )
    
    result = await seeker_service.update_seeker_status(user_id, action)
    
    return APIResponse(
        success=True,
        message=f"Seeker account status successfully updated to {action}",
        data=result
    )