from fastapi import APIRouter, HTTPException, status
from src.domains.category.schema.category_schema import CategoryResponse, CategoryRequest
from src.domains.category.services.admin_category_service import AdminCategoryService
from src.core.response import APIResponse

router = APIRouter(prefix="/api/admin/Category", tags=["Admin Category"])
router = APIRouter(prefix="/api/admin/Category", tags=["Admin Category"])

@router.post("/", response_model=APIResponse[CategoryResponse], status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryRequest):
    result = await AdminCategoryService.create(payload)
    return {
        "success": True,
        "message": "Category created successfully",
        "data": result
    }

@router.get("/", response_model=APIResponse[list[CategoryResponse]])
async def get_categories():
    result = await AdminCategoryService.get_all()
    return {
        "success": True,
        "message": "Categories fetched successfully",
        "data": result
    }

@router.put("/{category_id}", response_model=APIResponse[CategoryResponse])
async def update_category(category_id: str, payload: CategoryRequest):
    updated = await AdminCategoryService.update(category_id, payload)
    if not updated:
        raise HTTPException(
            status_code=400, 
            detail={"success": False, "message": "កែប្រែមិនបានជោគជ័យ ឬ ID មិនត្រឹមត្រូវ", "data": None}
        )
    return {
        "success": True,
        "message": "Category updated successfully",
        "data": updated
    }

@router.delete("/{category_id}", response_model=APIResponse[None])
async def delete_category(category_id: str):
    deleted = await AdminCategoryService.delete(category_id)
    if not deleted:
        raise HTTPException(
            status_code=404, 
            detail={"success": False, "message": "រកមិនឃើញ Category ឬ ID មិនត្រឹមត្រូវ", "data": None}
        )
    return {
        "success": True,
        "message": "Category deleted successfully",
        "data": None
    }