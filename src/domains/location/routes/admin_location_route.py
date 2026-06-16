from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional

# 🎯 ១. Import APIResponse របស់អ្នក
from src.core.response import APIResponse 

# Import Schemas
from src.dependencies.dependencies import RoleChecker
from src.domains.location.location_schema import (
    ProvinceRequest, ProvinceResponse, 
    DistrictRequest, DistrictResponse
)
import src.domains.location.services.admin_location_service as admin_service

# 🎯 ២. បង្កើតអថេរសម្រាប់ឆែកសិទ្ធិ (អនុញ្ញាតតែ "admin" ប៉ុណ្ណោះ)
require_admin = RoleChecker(["admin"])

router = APIRouter(
    prefix="/api/admin/locations",
    tags=["Admin Locations"],
    dependencies=[Depends(require_admin)]
)

# ==========================================
# 📍 Routes សម្រាប់ ខេត្ត/ក្រុង (Provinces)
# ==========================================

# 🎯 ២. កែប្រែ response_model ទៅជា APIResponse[ProvinceResponse]
@router.post("/provinces", response_model=APIResponse[ProvinceResponse], status_code=status.HTTP_201_CREATED)
async def create_province_route(data: ProvinceRequest):
    """Admin បង្កើតខេត្តថ្មី"""
    result = await admin_service.create_province(data)
    # 🎯 ៣. ខ្ចប់ទិន្នន័យដែល Service បោះមក ចូលទៅក្នុង APIResponse មុននឹង Return ទៅឱ្យ User
    return APIResponse(
        success=True,
        message="Province created successfully",
        data=result
    )

# 🎯 សម្រាប់ List ត្រូវដាក់ List នៅខាងក្នុង: APIResponse[List[ProvinceResponse]]
@router.get("/provinces", response_model=APIResponse[List[ProvinceResponse]])
async def get_all_provinces_route(
    # 🎯 កំណត់ Query Parameters ឱ្យ API
    search: Optional[str] = Query(None, description="ស្វែងរកតាមឈ្មោះខេត្ត (ខ្មែរ ឬអង់គ្លេស)"),
    is_active: Optional[bool] = Query(None, description="ចម្រោះយកតែខេត្តដែលបើក ឬបិទ (true/false)")
):
    """Admin ទាញយកបញ្ជីខេត្តទាំងអស់ (អាច Search និង Filter បាន)"""
    
    # បោះទិន្នន័យទៅឱ្យ Service
    result = await admin_service.get_all_provinces_admin(search=search, is_active=is_active)
    
    return APIResponse(
        success=True,
        message="ទាញយកបញ្ជីខេត្តជោគជ័យ",
        data=result
    )

@router.put("/provinces/{province_id}", response_model=APIResponse[ProvinceResponse])
async def update_province_route(province_id: str, data: ProvinceRequest):
    """Admin កែប្រែទិន្នន័យខេត្ត"""
    result = await admin_service.update_province(province_id, data)
    return APIResponse(
        success=True,
        message="Province updated successfully",
        data=result
    )

@router.delete("/provinces/{province_id}", response_model=APIResponse[ProvinceResponse])
async def delete_province_route(province_id: str):
    """Admin លុបខេត្ត (Soft Delete)"""
    result = await admin_service.delete_province(province_id)
    return APIResponse(
        success=True,
        message="Province deleted successfully",
        data=result
    )


# ==========================================
# 📍 Routes សម្រាប់ ស្រុក/ខណ្ឌ (Districts)
# ==========================================

@router.post("/districts", response_model=APIResponse[DistrictResponse], status_code=status.HTTP_201_CREATED)
async def create_district_route(data: DistrictRequest):
    """Admin បង្កើតស្រុកថ្មី"""
    result = await admin_service.create_district(data)
    return APIResponse(
        success=True,
        message="District created successfully",
        data=result
    )

@router.get("/provinces/{province_id}/districts", response_model=APIResponse[List[DistrictResponse]])
async def get_districts_by_province_route(
    province_id: str,
    search: Optional[str] = Query(None, description="ស្វែងរកតាមឈ្មោះស្រុក (ខ្មែរ ឬអង់គ្លេស)"),
    is_active: Optional[bool] = Query(None, description="ចម្រោះយកតែស្រុកដែលបើក ឬបិទ (true/false)")
):
    """Admin ទាញយកបញ្ជីស្រុកទាំងអស់នៅក្នុងខេត្តណាមួយ (អាច Search និង Filter បាន)"""
    result = await admin_service.get_districts_by_province_admin(
        province_id,
        search=search,
        is_active=is_active
    )
    return APIResponse(
        success=True,
        message="Districts retrieved successfully",
        data=result
    )

@router.put("/districts/{district_id}", response_model=APIResponse[DistrictResponse])
async def update_district_route(district_id: str, data: DistrictRequest):
    """Admin កែប្រែទិន្នន័យស្រុក"""
    result = await admin_service.update_district(district_id, data)
    return APIResponse(
        success=True,
        message="District updated successfully",
        data=result
    )

@router.delete("/districts/{district_id}", response_model=APIResponse[DistrictResponse])
async def delete_district_route(district_id: str):
    """Admin លុបស្រុក (Soft Delete)"""
    result = await admin_service.delete_district(district_id)
    return APIResponse(
        success=True,
        message="District deleted successfully",
        data=result
    )