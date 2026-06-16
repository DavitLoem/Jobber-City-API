from fastapi import APIRouter, Depends, Path, Query
from src.core.response import APIResponse
from src.domains.master_data.schemas.generic_master_data_schema import GenericMasterDataCreate, GenericMasterDataUpdate, GenericMasterDataResponse
from src.domains.master_data.services.generic_master_data_service import GenericMasterDataService
from src.core.mongo import job_levels_collection
from src.dependencies.dependencies import require_admin

job_level_service = GenericMasterDataService(collection=job_levels_collection)

router = APIRouter(
    prefix="/api/admin/master-data/job-levels",
    tags=["Admin - Master Data (Job Levels)"],
    dependencies=[Depends(require_admin)]
)

@router.get("/", response_model=APIResponse[list[GenericMasterDataResponse]])
async def get_all_job_levels(
    search: str = Query(None, description="ស្វែងរកតាមឈ្មោះកម្រិតការងារ"),
    status: str = Query("all", description="តម្រៀបតាម: 'all', 'active', ឬ 'inactive'")
):
    result = await job_level_service.get_all(search_term=search, status_filter=status)
    return APIResponse(success=True, message="Get all job levels successfully.", data=result)

@router.post("/", response_model=APIResponse[GenericMasterDataResponse])
async def create_job_level(payload: GenericMasterDataCreate):
    result = await job_level_service.create(payload)
    return APIResponse(success=True, message="Create job level successfully.", data=result)

@router.put("/{item_id}", response_model=APIResponse[GenericMasterDataResponse])
async def update_job_level(payload: GenericMasterDataUpdate, item_id: str = Path(...)):
    result = await job_level_service.update(item_id, payload)
    return APIResponse(success=True, message="Update job level successfully.", data=result)

@router.delete("/{item_id}", response_model=APIResponse[bool])
async def delete_job_level(item_id: str = Path(...)):
    await job_level_service.delete(item_id)
    return APIResponse(success=True, message="Delete job level successfully.", data=True)