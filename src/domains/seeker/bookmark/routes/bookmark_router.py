from fastapi import APIRouter, Depends, Path, Query
from src.core.response import APIResponse
from src.dependencies.dependencies import require_seeker
from src.domains.seeker.bookmark.services.bookmark_service import BookmarkService

bookmark_service = BookmarkService()
router = APIRouter(prefix="/api/seeker/jobs", tags=["Seeker - Bookmarks"])

@router.post("/{job_id}/bookmark", response_model=APIResponse)
async def toggle_bookmark_route(
    job_id: str = Path(..., description="ID នៃការងារដែលចង់ Save/Unsave"),
    current_user: dict = Depends(require_seeker)
):
    """ចុចម្តងដើម្បី Save ចុចម្តងទៀតដើម្បី Unsave (Toggle Bookmark)"""
    user_id = str(current_user["_id"])
    result = await bookmark_service.toggle_bookmark(user_id, job_id)
    
    return APIResponse(
        success=True, 
        message=result["message"], 
        data=result
    )

@router.get("/bookmarks/me", response_model=APIResponse)
async def get_saved_jobs_route(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(require_seeker)
):
    """ទាញយកបញ្ជីការងារទាំងអស់ដែលបានរក្សាទុក (Saved Jobs)"""
    user_id = str(current_user["_id"])
    result = await bookmark_service.get_saved_jobs(user_id, page=page, limit=limit)
    
    return APIResponse(
        success=True, 
        message="Get saved jobs successfully", 
        data=result
    )