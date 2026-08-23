from fastapi import APIRouter, Depends, File, Path, Query, UploadFile
from src.core.response import APIResponse

# 🎯 Import Role Checker សម្រាប់ Seeker
from src.dependencies.dependencies import require_seeker 

# 🎯 Import Service និង Schema 
from src.domains.employer.applicant.schemas.job_application_schema import ApplyJobRequest
from src.domains.profile.seeker_profile.services.attachment_service import upload_cover_letter
from src.domains.seeker.application.services.seeker_application_service import SeekerApplicationService

application_service = SeekerApplicationService()

# កំណត់ Router (ប្រើ Prefix នេះដើម្បីងាយស្រួលគ្រប់គ្រង)
router = APIRouter(
    prefix="/api/seeker", 
    tags=["Seeker - Application Management"]
)

# ==========================================
# 📍 ១. មុខងារដាក់ពាក្យការងារ (Apply Job)
# ==========================================
@router.post("/jobs/{job_id}/apply", response_model=APIResponse)
async def apply_job_route(
    payload: ApplyJobRequest,
    job_id: str = Path(..., description="ID នៃការងារដែលចង់ដាក់ពាក្យ"),
    current_user: dict = Depends(require_seeker)
):
    """
    អនុញ្ញាតឱ្យ Seeker ដាក់ពាក្យទៅកាន់ការងារណាមួយ។
    - តម្រូវឱ្យមាន CV (បញ្ជូនមកថ្មី ឬទាញពី Profile ក៏បាន)
    - កំណត់ត្រឹម 10 ការងារក្នុងមួយថ្ងៃ
    """
    user_id = str(current_user["_id"])
    
    # បញ្ជូនទិន្នន័យទៅ Service
    result = await application_service.apply_for_job(
        seeker_user_id=user_id, 
        job_id=job_id, 
        payload=payload
    )
    
    return APIResponse(
        success=True, 
        message=result["message"], 
        data=result # នឹងមានលោត remaining_quota ប្រាប់កូតាដែលនៅសល់
    )

# ==========================================
# 📍 ២. មុខងារមើលប្រវត្តិដាក់ពាក្យ (My Applications)
# ==========================================
@router.get("/applications/me", response_model=APIResponse)
async def get_my_applications_route(
    page: int = Query(1, ge=1, description="លេខទំព័រ"),
    limit: int = Query(10, ge=1, le=50, description="ចំនួនទិន្នន័យក្នុងមួយទំព័រ"),
    current_user: dict = Depends(require_seeker)
):
    """ទាញយកបញ្ជីការងារទាំងអស់ដែល Seeker បានដាក់ពាក្យ ដើម្បីតាមដាន Status (Pending, Reviewed, Interview...)"""
    
    user_id = str(current_user["_id"])
    
    result = await application_service.get_my_applications(
        seeker_user_id=user_id, 
        page=page, 
        limit=limit
    )
    
    return APIResponse(
        success=True, 
        message="Get my applications successfully", 
        data=result
    )
    
@router.get("/applications/{application_id}", response_model=APIResponse)
async def get_application_detail_route(
    application_id: str = Path(..., description="ID នៃការដាក់ពាក្យ (Application ID)"),
    current_user: dict = Depends(require_seeker)
):
    """
    ទាញយកព័ត៌មានលម្អិតនៃការដាក់ពាក្យរបស់ Seeker រួមមាន៖
    - ប្រវត្តិស្ថានភាព (Timeline)
    - ព័ត៌មានសម្ភាសន៍ (បើមាន)
    - Cover Letter និង Feedback
    """
    user_id = str(current_user["_id"])
    
    result = await application_service.get_application_detail(
        seeker_user_id=user_id, 
        application_id=application_id
    )
    
    return APIResponse(
        success=True, 
        message="Application details fetched successfully", 
        data=result
    )
    
@router.post("/cover-letter", response_model=APIResponse)
async def upload_cover_letter_endpoint(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_seeker) 
):
    """
    Upload ឯកសារ Cover Letter (PDF, DOC, DOCX) ទៅកាន់ Cloudinary។
    វានឹងត្រឡប់មកវិញនូវ URL សម្រាប់ឱ្យ App យកទៅបោះបន្តពេលហៅ API Apply Job។
    """
    # ហៅមុខងារពី Service ដើម្បីដំណើរការ Upload
    result = await upload_cover_letter(file)
    
    # បោះទិន្នន័យ (URL ថ្មី និងឈ្មោះឯកសារ) ត្រឡប់ទៅឱ្យ Frontend វិញ
    return APIResponse(
        success=True, 
        message="Cover letter uploaded successfully", 
        data=result
    )