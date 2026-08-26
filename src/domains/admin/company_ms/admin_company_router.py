from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from typing import Optional

from src.dependencies.dependencies import require_admin
from src.core.response import APIResponse

# នាំចូល Schemas ដែលបានបង្កើតមុននេះ
from src.domains.admin.company_ms.admin_company_schema import AdminCompanyListResponse, CompanyKpiResponse
from src.domains.admin.company_ms.admin_company_service import AdminCompanyService



router = APIRouter(
    prefix="/api/admin/companies",
    tags=["Admin - Companies Management"],
    dependencies=[Depends(require_admin)] # 🔒 ការពារ Route ទាំងមូលទាមទារសិទ្ធិ Admin
)

# បង្កើត Instance របស់ Service
company_service = AdminCompanyService()

# 🟢 ១. Route សម្រាប់ KPI Cards
@router.get("/kpis", response_model=APIResponse[CompanyKpiResponse])
async def get_company_kpis_route():
    """Admin ទាញយកទិន្នន័យ KPI Cards ទាំង ៤ (Total, Pending, Verified, Rejected)"""
    result = await company_service.get_company_kpis()
    return APIResponse(
        success=True,
        message="Company KPIs retrieved successfully",
        data=result
    )

# 🟢 ២. Route សម្រាប់តារាងបញ្ជីក្រុមហ៊ុន
@router.get("/", response_model=APIResponse[AdminCompanyListResponse])
async def get_company_list_route(
    search: Optional[str] = Query(None, description="ស្វែងរកតាមឈ្មោះក្រុមហ៊ុន"),
    status_filter: Optional[str] = Query(None, description="ចម្រោះយកតាម (pending, verified, rejected)"),
    page: int = Query(1, ge=1, description="ទំព័រទីប៉ុន្មាន"),
    limit: int = Query(10, ge=1, le=100, description="ចំនួនទិន្នន័យក្នុងមួយទំព័រ")
):
    """Admin ទាញយកបញ្ជីក្រុមហ៊ុន គួបផ្សំជាមួយការ Search និង Filter តាម Status"""
    result = await company_service.get_company_list(
        search=search, 
        status_filter=status_filter, 
        page=page, 
        limit=limit
    )
    return APIResponse(
        success=True,
        message="Company list retrieved successfully",
        data=result
    )

# 🟢 ៣. Route សម្រាប់ប៊ូតុង Approve / Reject លើ UI
@router.patch("/{company_id}/status", response_model=APIResponse)
async def update_company_status_route(
    company_id: str = Path(..., description="Object ID របស់ក្រុមហ៊ុន"),
    action: str = Query(..., description="សកម្មភាព (ត្រូវវាយ: approve ឬ reject)")
):
    """Admin អនុម័ត (Approve) ឬ បដិសេធ (Reject) ក្រុមហ៊ុន"""
    
    # Validation បឋមដើម្បីការពារការវាយ Action ខុស
    if action not in ["approve", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Action must be either 'approve' or 'reject'"
        )
    
    # ចំណាំ: កន្លែងនេះត្រូវហៅ Service ដើម្បី Update ចូល Database (យើងនឹងសរសេរ Logic វាបន្ទាប់)
    # result = await company_service.update_company_status(company_id, action)
    
    return APIResponse(
        success=True,
        message=f"Company status successfully updated to {action}",
        data=None
    )
    
@router.patch("/{company_id}/status", response_model=APIResponse)
async def update_company_status_route(
    company_id: str = Path(..., description="Object ID របស់ក្រុមហ៊ុន"),
    action: str = Query(..., description="សកម្មភាព (ត្រូវវាយ: approve ឬ reject)")
):
    """Admin អនុម័ត (Approve) ឬ បដិសេធ (Reject) ក្រុមហ៊ុន"""
    
    if action not in ["approve", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Action must be either 'approve' or 'reject'"
        )
    
    # 🎯 ហៅ Service ដែលយើងទើបសរសេរអម្បាញ់មិញ
    result = await company_service.update_company_status(company_id, action)
    
    return APIResponse(
        success=True,
        message=f"Company status successfully updated to {action}",
        data=result
    )