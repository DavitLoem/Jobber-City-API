from fastapi import APIRouter, Depends, Path, Query
from src.core.response import APIResponse

# 🎯 ១. Import Response Schema ចូលមក
from src.domains.master_data.schemas.generic_master_data_schema import (
    GenericMasterDataCreate, 
    GenericMasterDataUpdate,
    GenericMasterDataResponse
)
from src.domains.master_data.services.generic_master_data_service import GenericMasterDataService
from src.core.mongo import skills_collection
from src.dependencies.dependencies import require_admin

skill_service = GenericMasterDataService(collection=skills_collection)

router = APIRouter(
    prefix="/api/admin/master-data/skills",
    tags=["Admin - Master Data (Skills)"],
    dependencies=[Depends(require_admin)]
)

# 🎯 ២. ប្តូរពី [list[dict]] ទៅជា [list[GenericMasterDataResponse]]
@router.get("/", response_model=APIResponse[list[GenericMasterDataResponse]])
async def get_all_skills(
    search: str = Query(None, description="ស្វែងរកតាមឈ្មោះជំនាញ"),
    status: str = Query("all", description="តម្រៀបតាម: 'all', 'active', ឬ 'inactive'")
):
    """ទាញយកបញ្ជីជំនាញ (Skills) ទាំងអស់ ដោយមាន Search និង Filter"""
    
    # ហៅ Service ដោយបោះតម្លៃ search និង status ចូល
    result = await skill_service.get_all(search_term=search, status_filter=status)
    return APIResponse(success=True, message="Get all skills successfully.", data=result)

# 🎯 ៣. ប្តូរពី [dict] ទៅជា [GenericMasterDataResponse]
@router.post("/", response_model=APIResponse[GenericMasterDataResponse])
async def create_skill(payload: GenericMasterDataCreate):
    result = await skill_service.create(payload)
    return APIResponse(success=True, message="Create skill successfully.", data=result)

@router.put("/{item_id}", response_model=APIResponse[GenericMasterDataResponse])
async def update_skill(
    payload: GenericMasterDataUpdate,
    item_id: str = Path(...)
):
    result = await skill_service.update(item_id, payload)
    return APIResponse(success=True, message="Update skill successfully.", data=result)

@router.delete("/{item_id}", response_model=APIResponse[bool])
async def delete_skill(item_id: str = Path(...)):
    await skill_service.delete(item_id)
    return APIResponse(success=True, message="Delete skill successfully.", data=True)