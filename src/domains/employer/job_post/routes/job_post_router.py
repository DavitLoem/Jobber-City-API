from typing import List

from fastapi import APIRouter, Depends
from src.core.response import APIResponse

from src.domains.employer.job_post.schemas.job_post_schema import JobPostCreate, JobPostResponse, JobPostUpdate
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

@router.get("/", response_model=APIResponse[List[JobPostResponse]])
async def get_my_job_posts(
    current_user: dict = Depends(get_current_user)
):
    """ទាញយកបញ្ជីការងារទាំងអស់របស់ខ្លួនឯង"""
    
    user_id = str(current_user["_id"])
    result = await job_post_service.get_my_job_posts(user_id)
    
    return APIResponse(success=True, message="Get my job posts successfully", data=result)

@router.put("/{job_id}", response_model=APIResponse[JobPostResponse])
async def update_job_post(
    job_id: str,
    payload: JobPostUpdate,
    current_user: dict = Depends(get_current_user)
):
    """កែប្រែព័ត៌មានការងារ (អនុញ្ញាតតែម្ចាស់ការងារប៉ុណ្ណោះ)"""
    
    user_id = str(current_user["_id"])
    result = await job_post_service.update_job_post(user_id, job_id, payload)
    
    return APIResponse(success=True, message="Job Post updated successfully", data=result)

@router.delete("/{job_id}", response_model=APIResponse)
async def delete_job_post(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """លុបការងារចេញពីប្រព័ន្ធជាអចិន្ត្រៃយ៍ (Hard Delete)"""
    
    user_id = str(current_user["_id"])
    await job_post_service.delete_job_post(user_id, job_id)
    
    return APIResponse(success=True, message="Job Post deleted successfully")