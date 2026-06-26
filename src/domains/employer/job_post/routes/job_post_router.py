from fastapi import APIRouter, Depends
from src.core.response import APIResponse

from src.domains.employer.job_post.schemas.job_post_schema import JobPostCreate, JobPostResponse
from src.domains.employer.job_post.services.job_post_service import JobPostService

from src.dependencies.dependencies import require_employer, get_current_user

job_post_service = JobPostService()

# ១. អ្នកយាមទ្វារ (Guard): ការពារ Route ទាំងអស់ក្នុង File នេះ ឱ្យតែ Employer ទើបអាចចូលបាន
router = APIRouter(
    prefix="/api/employer/jobs",
    tags=["Employer - Job Post"],
    dependencies=[Depends(require_employer)] 
)

@router.post("/", response_model=APIResponse[JobPostResponse])
async def create_job_post(
    payload: JobPostCreate,
    current_user: dict = Depends(get_current_user) # ២. អ្នកយកទិន្នន័យ
):
    """បង្កើតការងារថ្មី (Create a new Job Post)"""
    
    # ទាញយក _id របស់ Employer
    user_id = str(current_user["_id"])
    
    # បញ្ជូនទៅ Service ធ្វើការ
    result = await job_post_service.create_job_post(user_id, payload)
    
    return APIResponse(success=True, message="Job Post created successfully", data=result)