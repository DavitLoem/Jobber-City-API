from fastapi import APIRouter, Query
from typing import List

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
    current_user: dict = Depends(get_current_user)
):
    """សម្រាប់បង្ហាញនៅ Section 'ការងារថ្មីៗ' (តម្រៀបតាមម៉ោង)"""
    user_id = str(current_user["_id"])
    result = await job_feed_service.get_jobs(user_id=user_id, feed_type="recent", page=page, limit=limit)
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