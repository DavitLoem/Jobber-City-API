from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from src.core.response import APIResponse

from src.domains.employer.job_post.schemas.job_post_schema import JobPostCreate, JobPostResponse, JobPostUpdate, JobStatusUpdate
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
    current_user: dict = Depends(get_current_user)
):
    """បង្កើតការងារថ្មី (Create a new Job Post)"""
    
    # ទាញយក _id របស់ Employer
    user_id = str(current_user["_id"])
    
    # បញ្ជូនទៅ Service ធ្វើការ
    result = await job_post_service.create_job_post(user_id, payload)
    
    return APIResponse(success=True, message="Job Post created successfully", data=result)

@router.get("/", response_model=APIResponse[List[JobPostResponse]])
async def get_my_job_posts(
    search: Optional[str] = Query(None, description="ស្វែងរកតាមចំណងជើងការងារ"),
    status: Optional[str] = Query(None, description="ត្រងតាមស្ថានភាព ឧ. active, closed, draft"),
    page: int = Query(1, ge=1, description="លេខទំព័រ"),
    limit: int = Query(10, ge=1, le=50, description="ចំនួនទិន្នន័យក្នុងមួយទំព័រ"),
    
    current_user: dict = Depends(require_employer) # 🎯 ឆែកថាគាត់ពិតជា Employer មែន
):
    """ទាញយកបញ្ជីការងារទាំងអស់របស់ខ្លួនឯង (មានគាំទ្រ Search, Filter Status & Pagination)"""
    
    user_id = str(current_user["_id"])
    
    # បញ្ជូនទិន្នន័យទៅឱ្យ Service ធ្វើការ
    result = await job_post_service.get_my_job_posts(
        user_id=user_id, 
        search=search, 
        status=status,
        page=page,
        limit=limit
    )
    
    return APIResponse(
        success=True, 
        message="Get my job posts successfully", 
        data=result
    )
    
@router.get("/{job_id}", response_model=APIResponse[JobPostResponse])
async def get_job_post_by_id(
    job_id: str = Path(...),
    current_user: dict = Depends(require_employer)
):
    """ទាញយកព័ត៌មានលម្អិតនៃការងារណាមួយតាមរយៈ ID"""
    
    user_id = str(current_user["_id"])
    
    # បញ្ជូនទៅ Service ធ្វើការ
    result = await job_post_service.get_job_post_by_id(user_id, job_id)
    
    return APIResponse(
        success=True, 
        message="Get job post successfully", 
        data=result
    )

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

@router.patch("/{job_id}/status", response_model=APIResponse)
async def update_job_status_route(
    payload: JobStatusUpdate,
    job_id: str = Path(...),
    current_user: dict = Depends(require_employer)
):
    """ប្តូរស្ថានភាពការងារ (ឧទាហរណ៍: ពី active ទៅ closed)"""
    user_id = str(current_user["_id"])
    
    result = await job_post_service.change_job_status(
        user_id=user_id, 
        job_id=job_id, 
        new_status=payload.status
    )
    
    return APIResponse(
        success=True, 
        message=f"Job status changed to {payload.status}", 
        data=result
    )