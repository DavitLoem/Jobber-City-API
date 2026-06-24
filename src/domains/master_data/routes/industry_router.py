from fastapi import APIRouter, Depends, Path, Query
from src.core.response import APIResponse
from src.domains.master_data.schemas.generic_master_data_schema import GenericMasterDataCreate, GenericMasterDataUpdate, GenericMasterDataResponse
from src.domains.master_data.services.generic_master_data_service import GenericMasterDataService
from src.core.mongo import industries_collection
from src.dependencies.dependencies import require_admin

industry_service = GenericMasterDataService(collection=industries_collection)

router = APIRouter(
    prefix="/api/admin/master-data/industries",
    tags=["Admin - Master Data (Industries)"],
    dependencies=[Depends(require_admin)]
)

@router.get("/", response_model=APIResponse[list[GenericMasterDataResponse]])
async def get_all_industry_types(
    search: str = Query(None, description="ស្វែងរកតាមឈ្មោះស្ថាប័ន"),
    status: str = Query("all", description="តម្រៀបតាម: 'all', 'active', ឬ 'inactive'") 
):
    result = await industry_service.get_all(search_term=search, status_filter=status)
    return APIResponse(success=True, message="Get all industry types successfully.", data=result)

@router.post("/", response_model=APIResponse[GenericMasterDataResponse])
async def create_industry(payload: GenericMasterDataCreate):
    result = await industry_service.create(payload)
    return APIResponse(success=True, message="Create industry successfully.", data=result)

@router.put("/{item_id}", response_model=APIResponse[GenericMasterDataResponse])
async def update_industry(payload: GenericMasterDataUpdate, item_id: str = Path(...)):
    result = await industry_service.update(item_id, payload)
    return APIResponse(success=True, message="Update industry successfully.", data=result)

@router.delete("/{item_id}", response_model=APIResponse[bool])
async def delete_industry(item_id: str = Path(...)):
    await industry_service.delete(item_id)
    return APIResponse(success=True, message="Delete industry successfully.", data=True)