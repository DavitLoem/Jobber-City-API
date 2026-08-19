from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List

from src.core.response import APIResponse
from src.domains.notification.services.notification_service import notification_service
from src.domains.notification.models.notification_model import FCMTokenRequest, UnreadCountResponse, NotificationResponse, NotificationListResponse
from src.dependencies.dependencies import get_current_user, require_mobile_users

router = APIRouter(
    prefix="/api/notifications",
    tags=["Core - Notifications"],
    dependencies=[Depends(require_mobile_users)]
)

# 🟢 API: យកចំនួនសារមិនទាន់អាន (Unread Count)
@router.get("/unread-count", response_model=APIResponse[UnreadCountResponse])
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user.get("_id", "")) if isinstance(current_user, dict) else str(current_user.id)
        count = await notification_service.get_unread_count(user_id)
        return APIResponse(success=True, message="Unread count fetched", data=UnreadCountResponse(count=count))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 🟢 API: យកបញ្ជី Notification ទាំងអស់
@router.get("/", response_model=APIResponse[NotificationListResponse])
async def get_notifications(
    limit: int = Query(20, ge=1, le=50),
    skip: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = str(current_user.get("_id", "")) if isinstance(current_user, dict) else str(current_user.id)
        notifications, total = await notification_service.get_my_notifications(user_id, limit, skip)
        
        data = NotificationListResponse(notifications=notifications, total=total)
        return APIResponse(success=True, message="Notifications fetched", data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 🟢 API: សម្គាល់ថាបានអានទាំងអស់ (Mark all as read)
@router.put("/mark-all-read", response_model=APIResponse[bool])
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    try:
        user_id = str(current_user.get("_id", "")) if isinstance(current_user, dict) else str(current_user.id)
        success = await notification_service.mark_all_as_read(user_id)
        return APIResponse(success=True, message="Marked all as read", data=success)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.put("/{notification_id}/read", response_model=APIResponse)
async def mark_single_notification_read(
    notification_id: str, 
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = str(current_user.get("_id", "")) if isinstance(current_user, dict) else str(current_user.id)
        
        success = await notification_service.mark_single_as_read(
            user_id=user_id, 
            notification_id=notification_id
        )
        
        if not success:
            # អាចមកពី ID ខុស ឬសារនោះមិនមែនជារបស់គាត់
            raise HTTPException(status_code=404, detail="Notification not found or you don't have access")
            
        return APIResponse(
            success=True, 
            message="Notification marked as read successfully", 
            data=True
        )
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/fcm-token", response_model=APIResponse)
async def update_user_fcm_token(
    request: FCMTokenRequest,
    current_user: dict = Depends(get_current_user) # ការពារសិទ្ធិ
):
    try:
        user_id = str(current_user.get("_id", ""))
        await notification_service.update_fcm_token(user_id, request.fcm_token)
        return APIResponse(success=True, message="FCM Token updated successfully", data=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))