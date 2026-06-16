from fastapi import APIRouter, Depends
from src.core.response import APIResponse

# 🎯 Import Schemas និង Service
from src.domains.profile.company_profile.schemas.company_profile_schema import (
    CompanyProfileCreate,
    CompanyProfileUpdate,
    CompanyProfileResponse
)
from src.domains.profile.company_profile.services.company_profile_service import CompanyProfileService

# 🎯 Import ទាំងពីរមក (Guard និង Data Fetcher)
from src.dependencies.dependencies import require_employer, get_current_user

# បង្កើត Service Object
company_profile_service = CompanyProfileService()

# ១. អ្នកយាមទ្វារ (Guard): ការពារ Route ទាំងអស់ក្នុង File នេះ
router = APIRouter(
    prefix="/api/employer/company-profile",
    tags=["Employer - Company Profile"],
    dependencies=[Depends(require_employer)] 
)

@router.get("/me", response_model=APIResponse[CompanyProfileResponse])
async def get_my_company_profile(
    current_user: dict = Depends(get_current_user) # ២. អ្នកយកទិន្នន័យ
):
    """ទាញយកព័ត៌មានក្រុមហ៊ុនរបស់ Employer ដែលកំពុង Login"""
    
    # ✅ ដោះស្រាយ Error: ប្តូរ "id" ទៅ "_id" ព្រោះ MongoDB ប្រើ _id
    user_id = str(current_user["_id"]) 
    
    result = await company_profile_service.get_my_company_profile(user_id)
    return APIResponse(success=True, message="Get my company profile successfully", data=result)


@router.post("/", response_model=APIResponse[CompanyProfileResponse])
async def create_company_profile(
    payload: CompanyProfileCreate,
    current_user: dict = Depends(get_current_user) # ២. អ្នកយកទិន្នន័យ
):
    """បង្កើតព័ត៌មានក្រុមហ៊ុនថ្មី (អនុញ្ញាតត្រឹមតែ ១ ដងគត់ក្នុង ១ គណនី)"""
    
    # ✅ ដោះស្រាយ Error: ប្តូរមកប្រើ "_id"
    user_id = str(current_user["_id"])
    result = await company_profile_service.create_company_profile(user_id, payload)
    
    return APIResponse(success=True, message="Create company profile successfully", data=result)


@router.put("/", response_model=APIResponse[CompanyProfileResponse])
async def update_company_profile(
    payload: CompanyProfileUpdate,
    current_user: dict = Depends(get_current_user) # ២. អ្នកយកទិន្នន័យ
):
    """កែប្រែព័ត៌មានក្រុមហ៊ុនរបស់ខ្លួនឯង"""
    
    # ✅ ដោះស្រាយ Error: ប្តូរមកប្រើ "_id"
    user_id = str(current_user["_id"])
    result = await company_profile_service.update_company_profile(user_id, payload)
    
    return APIResponse(success=True, message="Update company profile successfully", data=result)