from fastapi import APIRouter, Depends
from src.core.response import APIResponse

from src.core.mongo import (
    skills_collection,
    job_levels_collection,
    education_levels_collection,
    employment_types_collection,
    work_types_collection,
    industries_collection
)
from src.domains.master_data.services.generic_master_data_service import GenericMasterDataService
from src.dependencies.dependencies import require_mobile_users

router = APIRouter(
    prefix="/api/master-data",
    tags=["Mobile - Master Data Dropdowns"],
    dependencies=[Depends(require_mobile_users)]
)

# 🎯 ៣. បង្កើត Instance របស់ Service សម្រាប់ Collection នីមួយៗ
skills_service = GenericMasterDataService(skills_collection)
job_levels_service = GenericMasterDataService(job_levels_collection)
education_levels_service = GenericMasterDataService(education_levels_collection)
employment_types_service = GenericMasterDataService(employment_types_collection)
work_types_service = GenericMasterDataService(work_types_collection)
industries_service = GenericMasterDataService(industries_collection)

# ==========================================
# 📍 Routes សម្រាប់ Mobile App ទាញយកទៅបង្ហាញជា Dropdown
# ==========================================

@router.get("/skills")
async def get_active_skills(search: str = None):
    # កំណត់ status_filter="active" ជានិច្ច ដើម្បីកុំឱ្យលោតទិន្នន័យដែល Admin បិទចោល
    data = await skills_service.get_all(search_term=search, status_filter="active")
    return APIResponse(success=True, message="Get active skills", data=data)

@router.get("/job-levels")
async def get_active_job_levels():
    data = await job_levels_service.get_all(status_filter="active")
    return APIResponse(success=True, message="Get active job levels", data=data)

@router.get("/education-levels")
async def get_active_education_levels():
    data = await education_levels_service.get_all(status_filter="active")
    return APIResponse(success=True, message="Get active education levels", data=data)

@router.get("/employment-types")
async def get_active_employment_types():
    data = await employment_types_service.get_all(status_filter="active")
    return APIResponse(success=True, message="Get active employment types", data=data)

@router.get("/work-types")
async def get_active_work_types():
    data = await work_types_service.get_all(status_filter="active")
    return APIResponse(success=True, message="Get active work types", data=data)

@router.get("/industries")
async def get_active_industries():
    data = await industries_service.get_all(status_filter="active")
    return APIResponse(success=True, message="Get active industries", data=data)