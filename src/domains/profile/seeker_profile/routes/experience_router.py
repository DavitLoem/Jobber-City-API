from fastapi import APIRouter, Depends, Path
from src.core.response import APIResponse

# 🎯 Import Schemas និង Service 
from src.domains.profile.seeker_profile.schema.sub_schema import ExperienceRequest
import src.domains.profile.seeker_profile.services.experience_service as exp_service

# 🎯 Import Auth 
from src.dependencies.dependencies import require_seeker

router = APIRouter(
    prefix="/api/seeker/profile/experiences",
    tags=["Seeker - Profile Experiences"],
    dependencies=[Depends(require_seeker)]
)

@router.post("/", response_model=APIResponse[dict])
async def add_experience_route(
    payload: ExperienceRequest,
    current_user: dict = Depends(require_seeker)
):
    """បន្ថែមបទពិសោធន៍ការងារថ្មីមួយ (Add New Experience)"""
    user_id = current_user.get("id") or current_user.get("_id")
    
    result = await exp_service.add_experience(str(user_id), payload)
    
    return APIResponse(
        success=True,
        message="Experience added successfully",
        data=result
    )

@router.put("/{exp_id}", response_model=APIResponse[dict])
async def update_experience_route(
    payload: ExperienceRequest,
    exp_id: str = Path(..., description="ID របស់បទពិសោធន៍ដែលចង់កែប្រែ"),
    current_user: dict = Depends(require_seeker)
):
    """កែប្រែព័ត៌មានបទពិសោធន៍ការងារចាស់ (Update Existing Experience)"""
    user_id = current_user.get("id") or current_user.get("_id")
    
    result = await exp_service.update_experience(str(user_id), exp_id, payload)
    
    return APIResponse(
        success=True,
        message="Experience updated successfully",
        data=result
    )

@router.delete("/{exp_id}", response_model=APIResponse[bool])
async def delete_experience_route(
    exp_id: str = Path(..., description="ID របស់បទពិសោធន៍ដែលចង់លុប"),
    current_user: dict = Depends(require_seeker)
):
    """លុបបទពិសោធន៍ការងារចេញពីប្រវត្តិរូប (Delete Experience)"""
    user_id = current_user.get("id") or current_user.get("_id")
    
    await exp_service.delete_experience(str(user_id), exp_id)
    
    return APIResponse(
        success=True,
        message="Experience deleted successfully",
        data=True
    )