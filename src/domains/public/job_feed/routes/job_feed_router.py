from fastapi import APIRouter, Query
from typing import List
from src.core.response import APIResponse

# 🎯 Import Schema និង Service ដែលយើងទើបតែបង្កើត
from src.domains.public.job_feed.schemas.job_feed_schema import JobFeedResponse
from src.domains.public.job_feed.services.job_feed_service import JobFeedService

# បង្កើត Service Object
job_feed_service = JobFeedService()

router = APIRouter(
    prefix="/api/public/jobs",
    tags=["Public - Job Feed"]
)

@router.get("/", response_model=APIResponse[List[JobFeedResponse]])
async def get_recent_jobs(
    # ប្រើ Query ដើម្បីទទួលយក Parameter ពី URL (ឧ. ?page=1&limit=10)
    page: int = Query(1, ge=1, description="លេខទំព័រ (ចាប់ផ្តើមពី 1)"),
    limit: int = Query(10, ge=1, le=50, description="ចំនួនការងារក្នុងមួយទំព័រ (អតិបរមា 50)")
):
    """
    ទាញយកបញ្ជីការងារថ្មីៗ (Recent Jobs)
    - មិនទាមទារ Token (Public API)
    - ទិន្នន័យត្រូវបានតម្រៀបពីថ្មីទៅចាស់ដោយស្វ័យប្រវត្តិ
    """
    
    # ហៅ Service ឱ្យទាញទិន្នន័យ
    result = await job_feed_service.get_recent_jobs(page=page, limit=limit)
    
    return APIResponse(success=True, message="Get recent jobs successfully", data=result)