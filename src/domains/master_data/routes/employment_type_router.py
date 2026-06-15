from fastapi import APIRouter, Depends, Path
from fastapi.params import Query
from src.core.response import APIResponse
from src.domains.master_data.schemas.generic_master_data_schema import GenericMasterDataCreate, GenericMasterDataUpdate, GenericMasterDataResponse
from src.domains.master_data.services.generic_master_data_service import GenericMasterDataService
from src.core.mongo import employment_types_collection
from src.dependencies.dependencies import require_admin

employment_type_service = GenericMasterDataService(collection=employment_types_collection)

router = APIRouter(
    prefix="/api/admin/master-data/employment-types",
    tags=["Admin - Master Data (Employment Types)"],
    dependencies=[Depends(require_admin)]
)

@router.get("/", response_model=APIResponse[list[GenericMasterDataResponse]])
async def get_all_employment_types(
    search: str = Query(None, description="ស្វែងរកតាមឈ្មោះប្រភេទការងារ"),
    status: str = Query("all", description="តម្រៀបតាម: 'all', 'active', ឬ 'inactive'")
):
    result = await employment_type_service.get_all(search_term=search, status_filter=status)
    return APIResponse(success=True, message="Get all employment types successfully.", data=result)

@router.post("/", response_model=APIResponse[GenericMasterDataResponse])
async def create_employment_type(payload: GenericMasterDataCreate):
    result = await employment_type_service.create(payload)
    return APIResponse(success=True, message="Create employment type successfully.", data=result)

@router.put("/{item_id}", response_model=APIResponse[GenericMasterDataResponse])
async def update_employment_type(payload: GenericMasterDataUpdate, item_id: str = Path(...)):
    result = await employment_type_service.update(item_id, payload)
    return APIResponse(success=True, message="Update employment type successfully.", data=result)

@router.delete("/{item_id}", response_model=APIResponse[bool])
async def delete_employment_type(item_id: str = Path(...)):
    await employment_type_service.delete(item_id)
    return APIResponse(success=True, message="Delete employment type successfully.", data=True)