from fastapi import APIRouter, Depends, UploadFile, File
from src.core.response import APIResponse

# 🎯 Import Service
import src.domains.profile.seeker_profile.services.attachment_service as attachment_service
from src.domains.profile.seeker_profile.schema.core_schema import SeekerProfileResponse

# 🎯 Import Auth
from src.dependencies.dependencies import require_seeker

router = APIRouter(
    prefix="/api/seeker/profile",
    tags=["Mobile - Seeker Profile"],
    dependencies=[Depends(require_seeker)]
)

@router.post("/upload-image", response_model=APIResponse[SeekerProfileResponse])
async def upload_profile_image_route(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_seeker)
):
    """
    Upload ឬផ្លាស់ប្តូររូបថត Profile របស់ Seeker។
    ទាមទារការបញ្ជូនទិន្នន័យជាទម្រង់ 'multipart/form-data'។
    """
    user_id = current_user.get("id") or current_user.get("_id")
    
    result = await attachment_service.upload_profile_image(str(user_id), file)
    
    return APIResponse(
        success=True,
        message="Profile image uploaded successfully",
        data=result
    )
    
@router.post("/upload-cv", response_model=APIResponse[dict]) # 🎯 ប្តូរ Response Model
async def upload_cv_and_extract_route( # 🎯 ប្តូរឈ្មោះមុខងារឱ្យត្រូវនឹង Flow ថ្មី
    file: UploadFile = File(...),
    current_user: dict = Depends(require_seeker)
):
    """
    Upload CV ជាទម្រង់ PDF។ 
    ប្រព័ន្ធនឹងប្រើ AI ពិនិត្យភាពត្រឹមត្រូវ Upload រួចបោះទិន្នន័យ (JSON) ត្រឡប់ទៅ Frontend ដើម្បីផ្ទៀងផ្ទាត់។
    """
    user_id = current_user.get("id") or current_user.get("_id")
    
    # 🎯 ហៅមុខងារថ្មី
    result = await attachment_service.process_and_extract_cv(str(user_id), file)
    
    return APIResponse(
        success=True,
        message="CV processed successfully. Please review the extracted data.",
        data=result
    )