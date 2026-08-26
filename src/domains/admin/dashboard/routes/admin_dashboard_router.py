from fastapi import APIRouter, Depends, Query, status

from src.dependencies.dependencies import require_admin 
from src.core.response import APIResponse

# សន្មតថាយើងដាក់ Schema នៅទីនេះ
from src.domains.admin.dashboard.service.dashboard_services import get_dashboard_kpi_summary, get_platform_growth, get_jobs_by_category
# សន្មតថាយើងដាក់ Service នៅទីនេះ
from src.domains.admin.dashboard.schema.dashboard_schemas import JobsCategoryResponse, KPISummaryResponse, PlatformGrowthResponse

router = APIRouter(
    prefix="/api/admin/dashboard",
    tags=["Admin - Dashboard"],
    dependencies=[Depends(require_admin)] # 🔒 ការពារដោយតម្រូវឱ្យមានសិទ្ធិជា Admin
)

@router.get("/kpi-summary", response_model=APIResponse[KPISummaryResponse])
async def get_kpi_summary_route():
    """Admin ទាញយកទិន្នន័យសង្ខេបសម្រាប់ KPI Cards ទាំង ៤ នៅលើ Dashboard"""
    
    # ហៅ Service ដើម្បីធ្វើការគណនាទិន្នន័យ
    result = await get_dashboard_kpi_summary()
    
    # វេចខ្ចប់ទិន្នន័យទៅក្នុង APIResponse ស្តង់ដារ
    return APIResponse(
        success=True,
        message="KPI summary retrieved successfully",
        data=result
    )

@router.get("/growth-chart", response_model=APIResponse[PlatformGrowthResponse])
async def get_platform_growth_route(
    months: int = Query(6, description="ចំនួនខែដែលចង់មើលត្រឡប់ក្រោយ (ឧ. 6)")
):
    """Admin ទាញយកទិន្នន័យកំណើនអ្នកប្រើប្រាស់ សម្រាប់ Line Chart"""
    result = await get_platform_growth(months=months)
    return APIResponse(
        success=True,
        message="Platform growth data retrieved successfully",
        data=result
    )

@router.get("/jobs-by-category", response_model=APIResponse[JobsCategoryResponse])
async def get_jobs_by_category_route():
    """Admin ទាញយកភាគរយការងារតាមប្រភេទកំពូលៗ សម្រាប់ Donut Chart"""
    result = await get_jobs_by_category()
    return APIResponse(
        success=True,
        message="Jobs by category data retrieved successfully",
        data=result
    )