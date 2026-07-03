from fastapi import APIRouter, Depends, Request
from src.core.response import APIResponse

# 🎯 Import Schemas និង Service របស់អ្នក
from src.domains.profile.seeker_profile.schema.core_schema import SeekerCoreProfileUpdateRequest, SeekerProfileResponse
import src.domains.profile.seeker_profile.services.core_profile_service as profile_service

# 🎯 Import Auth & Role Checker
from src.dependencies.dependencies import require_seeker

router = APIRouter(
    prefix="/api/seeker/profile",
    tags=["Mobile - Seeker Profile"],
    dependencies=[Depends(require_seeker)] # ចាក់សោរ Router នេះទាំងមូល
)

@router.get("/", response_model=APIResponse[SeekerProfileResponse])
async def get_profile_route(current_user: dict = Depends(require_seeker)):
    """ទាញយកប្រវត្តិរូប (Profile) ទាំងមូលរបស់ Seeker"""
    
    # ចំណាំ: អាស្រ័យលើរបៀបដែល RoleChecker របស់អ្នក Return ទិន្នន័យត្រឡប់មកវិញ 
    # វាអាចជា current_user["id"], current_user["_id"] ឬ current_user.id
    user_id = current_user.get("id") or current_user.get("_id") 
    
    result = await profile_service.get_seeker_profile(str(user_id))
    
    return APIResponse(
        success=True,
        message="Get profile successfully",
        data=result
    )

@router.put("/core", response_model=APIResponse[SeekerProfileResponse])
async def update_core_profile_route(
    payload: SeekerCoreProfileUpdateRequest, 
    current_user: dict = Depends(require_seeker)
):
    """កែប្រែព័ត៌មានផ្ទាល់ខ្លួន ឬចំណង់ចំណូលចិត្តការងារ"""
    
    user_id = current_user.get("id") or current_user.get("_id")
    
    result = await profile_service.update_core_profile(str(user_id), payload)
    
    return APIResponse(
        success=True,
        message="Update core profile successfully",
        data=result
    )
    
@router.put("/onboarding", response_model=APIResponse[SeekerProfileResponse])
async def complete_onboarding_route(
    payload: SeekerCoreProfileUpdateRequest, 
    current_user: dict = Depends(require_seeker)
):
    """បញ្ចប់ការចុះឈ្មោះជំហានដំបូង (Onboarding)"""
    user_id = current_user.get("id") or current_user.get("_id")
    
    # ហៅ Service ដដែល (វាមាន logic រួចហើយ)
    result = await profile_service.update_core_profile(str(user_id), payload)
    
    return APIResponse(
        success=True,
        message="Onboarding completed successfully",
        data=result
    )