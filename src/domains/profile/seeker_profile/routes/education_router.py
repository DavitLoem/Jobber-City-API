from fastapi import APIRouter, Depends, Path
from src.core.response import APIResponse

from src.domains.profile.seeker_profile.schema.sub_schema import EducationRequest
import src.domains.profile.seeker_profile.services.education_service as edu_service
from src.dependencies.dependencies import RoleChecker

require_seeker = RoleChecker(["seeker"])

router = APIRouter(
    prefix="/api/seeker/profile/educations",
    tags=["Mobile - Seeker Educations"],
    dependencies=[Depends(require_seeker)]
)

@router.post("/", response_model=APIResponse[dict])
async def add_education_route(payload: EducationRequest, current_user: dict = Depends(require_seeker)):
    user_id = current_user.get("id") or current_user.get("_id")
    result = await edu_service.add_education(str(user_id), payload)
    return APIResponse(success=True, message="Education added successfully", data=result)

@router.put("/{edu_id}", response_model=APIResponse[dict])
async def update_education_route(
    payload: EducationRequest,
    edu_id: str = Path(...),
    current_user: dict = Depends(require_seeker)
):
    user_id = current_user.get("id") or current_user.get("_id")
    result = await edu_service.update_education(str(user_id), edu_id, payload)
    return APIResponse(success=True, message="Education updated successfully", data=result)

@router.delete("/{edu_id}", response_model=APIResponse[bool])
async def delete_education_route(edu_id: str = Path(...), current_user: dict = Depends(require_seeker)):
    user_id = current_user.get("id") or current_user.get("_id")
    await edu_service.delete_education(str(user_id), edu_id)
    return APIResponse(success=True, message="Education deleted successfully", data=True)