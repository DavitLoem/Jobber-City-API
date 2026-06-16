from fastapi import APIRouter, Depends, Path, Query
from src.core.response import APIResponse
from src.domains.master_data.schemas.generic_master_data_schema import GenericMasterDataCreate, GenericMasterDataUpdate, GenericMasterDataResponse
from src.domains.master_data.services.generic_master_data_service import GenericMasterDataService
from src.core.mongo import work_types_collection
from src.dependencies.dependencies import require_admin

work_type_service = GenericMasterDataService(collection=work_types_collection)

router = APIRouter(
    prefix="/api/admin/master-data/work-types",
    tags=["Admin - Master Data (Work Types)"],
    dependencies=[Depends(require_admin)]
)

@router.get("/", response_model=APIResponse[list[GenericMasterDataResponse]])
async def get_all_work_types(
    search: str = Query(None, description="ស្វែងរកតាមឈ្មោះប្រភេទការងារ"),
    status: str = Query("all", description="តម្រៀបតាម: 'all', 'active', ឬ 'inactive'") 
):
    result = await work_type_service.get_all(search_term=search, status_filter=status)
    return APIResponse(success=True, message="Get all work types successfully.", data=result)

@router.post("/", response_model=APIResponse[GenericMasterDataResponse])
async def create_work_type(payload: GenericMasterDataCreate):
    result = await work_type_service.create(payload)
    return APIResponse(success=True, message="Create work type successfully.", data=result)

@router.put("/{item_id}", response_model=APIResponse[GenericMasterDataResponse])
async def update_work_type(payload: GenericMasterDataUpdate, item_id: str = Path(...)):
    result = await work_type_service.update(item_id, payload)
    return APIResponse(success=True, message="Update work type successfully.", data=result)

@router.delete("/{item_id}", response_model=APIResponse[bool])
async def delete_work_type(item_id: str = Path(...)):
    await work_type_service.delete(item_id)
    return APIResponse(success=True, message="Delete work type successfully.", data=True)