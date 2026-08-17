from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from src.core.response import APIResponse
from src.dependencies.dependencies import get_current_user
from src.domains.employer.employer_dashboard.models.employer_dashboard_model import EmployerDashboardResponse
from src.domains.employer.employer_dashboard.services import employer_dashboard_service
from src.dependencies.dependencies import require_employer


router = APIRouter(
    prefix="/api/employer/dashboard",
    tags=["Employer Dashboard"],
    dependencies=[Depends(require_employer)] 
)

@router.get("/overview", response_model=APIResponse[EmployerDashboardResponse])
async def get_dashboard_overview(
    filter: Optional[str] = Query("this_month", description="Timeframe filter: today, this_week, this_month, 2026-08, etc."),
    current_user: dict = Depends(get_current_user) # ចាប់យក User ដែលកំពុង Login
):
    try:
        # ចាប់យក user_id ពី current_user (អាស្រ័យលើទម្រង់ Auth របស់អ្នក អាចជា current_user["_id"] ឬ current_user.id)
        user_id = str(current_user.get("_id", "")) if isinstance(current_user, dict) else str(current_user.id)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized user")

        # ហៅ Service ដើម្បីទាញយកទិន្នន័យ
        dashboard_data = await employer_dashboard_service.get_dashboard_data(
            user_id=user_id,
            filter_str=filter
        )
        
        return APIResponse(success=True, message="Dashboard data fetched", data=dashboard_data)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))