from fastapi import APIRouter, Depends, Query # 🎯 Import Query
from typing import List, Optional # 🎯 Import Optional

from src.core.response import APIResponse
from src.dependencies.dependencies import require_mobile_users
from src.domains.location.location_schema import ProvinceResponse, DistrictResponse
import src.domains.location.services.mobile_location_service as mobile_service

router = APIRouter(
    prefix="/api/locations",
    tags=["Mobile - Locations"],
    dependencies=[Depends(require_mobile_users)]
)

@router.get("/provinces", response_model=APIResponse[List[ProvinceResponse]])
async def get_mobile_provinces_route(
    # 🎯 ទទួលយក Query Parameter (search)
    search: Optional[str] = Query(None, description="ស្វែងរកតាមឈ្មោះខេត្ត (ខ្មែរ ឬអង់គ្លេស)")
):
    """App ទាញយកបញ្ជីខេត្តទាំងអស់ (សម្រាប់ Dropdown)"""
    result = await mobile_service.get_active_provinces(search=search)
    return APIResponse(
        success=True,
        message="Get provinces successfully",
        data=result
    )

@router.get("/provinces/{province_id}/districts", response_model=APIResponse[List[DistrictResponse]])
async def get_mobile_districts_route(
    province_id: str,
    # 🎯 ទទួលយក Query Parameter (search)
    search: Optional[str] = Query(None, description="ស្វែងរកតាមឈ្មោះស្រុក (ខ្មែរ ឬអង់គ្លេស)")
):
    """App ទាញយកបញ្ជីស្រុកយោងតាមខេត្ត (សម្រាប់ Dropdown)"""
    result = await mobile_service.get_active_districts_by_province(province_id, search=search)
    return APIResponse(
        success=True,
        message="Get districts successfully",
        data=result
    )