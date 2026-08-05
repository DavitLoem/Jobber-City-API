from fastapi import APIRouter, Query
from typing import List, Optional

from fastapi.params import Depends
from src.core.response import APIResponse

from src.domains.seeker.job_feed.schemas.job_feed_schema import JobFeedResponse
from src.domains.seeker.job_feed.services.job_feed_service import JobFeedService
from src.dependencies.dependencies import get_current_user, require_seeker

# បង្កើត Service Object
job_feed_service = JobFeedService()

router = APIRouter(
    prefix="/api/seeker/jobs",
    tags=["Seeker - Job Feed"],
    dependencies=[Depends(require_seeker)]
)

@router.get("/recent", response_model=APIResponse[List[JobFeedResponse]])
async def get_recent_jobs_route(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    category_id: Optional[str] = Query(None, description="ID របស់ Category សម្រាប់ Filter"), # 🎯 បន្ថែមទីនេះ
    current_user: dict = Depends(get_current_user)
):
    """សម្រាប់បង្ហាញនៅ Section 'ការងារថ្មីៗ' (តម្រៀបតាមម៉ោង)"""
    user_id = str(current_user["_id"])
    
    # 🎯 បញ្ជូន category_id ទៅ Service
    result = await job_feed_service.get_jobs(
        user_id=user_id, 
        feed_type="recent", 
        page=page, 
        limit=limit,
        category_id=category_id 
    )
    return APIResponse(success=True, message="Get recent jobs", data=result)

@router.get("/recommended", response_model=APIResponse[List[JobFeedResponse]])
async def get_recommended_jobs_route(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """សម្រាប់បង្ហាញនៅ Section 'ការងារស័ក្តិសមនឹងអ្នក' (តម្រៀបតាមភាគរយ)"""
    user_id = str(current_user["_id"])
    result = await job_feed_service.get_jobs(user_id=user_id, feed_type="recommended", page=page, limit=limit)
    return APIResponse(success=True, message="Get recommended jobs", data=result)

@router.get("/search", response_model=APIResponse[List[JobFeedResponse]])
async def search_job_feeds(
    keyword: str = Query(..., description="ពាក្យគន្លឹះសម្រាប់ស្វែងរក"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    service: JobFeedService = Depends()
):
    """API សម្រាប់ស្វែងរកការងារតាមរយៈពាក្យគន្លឹះ (Title, Company, Skills)"""
    user_id = current_user["user_id"]
    
    jobs = await service.search_jobs(
        user_id=user_id,
        keyword=keyword,
        page=page,
        limit=limit
    )
    
    return APIResponse(
        success=True,
        message="Search results fetched successfully",
        data=jobs
    )