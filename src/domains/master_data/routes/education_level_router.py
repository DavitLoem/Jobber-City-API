from fastapi import APIRouter, Depends, Path, Query
from src.core.response import APIResponse
from src.domains.master_data.schemas.generic_master_data_schema import GenericMasterDataCreate, GenericMasterDataUpdate, GenericMasterDataResponse
from src.domains.master_data.services.generic_master_data_service import GenericMasterDataService
from src.core.mongo import education_levels_collection
from src.dependencies.dependencies import require_admin

education_level_service = GenericMasterDataService(collection=education_levels_collection)

router = APIRouter(
    prefix="/api/admin/master-data/education-levels",
    tags=["Admin - Master Data (Education Levels)"],
    dependencies=[Depends(require_admin)]
)

@router.get("/", response_model=APIResponse[list[GenericMasterDataResponse]])
async def get_all_education_levels(
    search: str = Query(None, description="ស្វែងរកតាមឈ្មោះជំនាញ"),
    status: str = Query("all", description="តម្រៀបតាម: 'all', 'active', ឬ 'inactive'")
):
    result = await education_level_service.get_all(search_term=search, status_filter=status)
    return APIResponse(success=True, message="Get all education levels successfully.", data=result)

@router.post("/", response_model=APIResponse[GenericMasterDataResponse])
async def create_education_level(payload: GenericMasterDataCreate):
    result = await education_level_service.create(payload)
    return APIResponse(success=True, message="Create education level successfully.", data=result)

@router.put("/{item_id}", response_model=APIResponse[GenericMasterDataResponse])
async def update_education_level(payload: GenericMasterDataUpdate, item_id: str = Path(...)):
    result = await education_level_service.update(item_id, payload)
    return APIResponse(success=True, message="Update education level successfully.", data=result)

@router.delete("/{item_id}", response_model=APIResponse[bool])
async def delete_education_level(item_id: str = Path(...)):
    await education_level_service.delete(item_id)
    return APIResponse(success=True, message="Delete education level successfully.", data=True)