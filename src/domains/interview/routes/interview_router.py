from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from src.core.response import APIResponse

from src.domains.interview.schema.interview_schema import (
    ScheduleInterviewRequest,
    RescheduleInterviewRequest,
    CancelInterviewRequest,
    InterviewResponse,
    JoinInterviewResponse,
)
from src.domains.interview.services.interview_service import interview_service
from src.dependencies.dependencies import get_current_user, require_employer, require_mobile_users

# 🎯 មានតែ Seeker & Employer ទេ ដែលចូលប្រើមុខងារនេះបាន (ដូច Chat) — ប៉ុន្តែមុខងារ
# Schedule/Reschedule ត្រូវការសិទ្ធិ Employer ជាក់លាក់បន្ថែម (មើលក្នុងខ្លួន Route)
router = APIRouter(
    prefix="/api/interviews",
    tags=["Mobile - Online Interview (Video Call)"],
    dependencies=[Depends(require_mobile_users)],
)


@router.post("/", response_model=APIResponse[InterviewResponse])
async def schedule_interview(
    payload: ScheduleInterviewRequest,
    current_user: dict = Depends(require_employer),
):
    """
    Employer ណាត់សម្ភាសន៍តាម Video Call ជាមួយ Seeker ណាមួយ (មិនកំណត់ត្រឹមតែ Seeker
    ដែលធ្លាប់ដាក់ពាក្យទេ) — បង្កើត Jitsi Meet Room ដោយស្វ័យប្រវត្តិ ហើយផ្ញើ Push
    Notification ទៅ Seeker ភ្លាមៗ។
    """
    result = await interview_service.schedule_interview(current_user, payload)
    return APIResponse(success=True, message="Interview scheduled successfully", data=result)


@router.get("/", response_model=APIResponse[List[InterviewResponse]])
async def list_my_interviews(
    status: Optional[str] = Query("all", description="ត្រង: all, scheduled, ongoing, completed, cancelled, no_show"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """ទាញយកគ្រប់ Interview ដែល User បច្ចុប្បន្នជាសមាជិក (Seeker ឬ Employer) តម្រៀបតាមម៉ោងណាត់ជិតបំផុតមុន"""
    result = await interview_service.list_interviews(str(current_user["_id"]), status, page, limit)
    return APIResponse(success=True, message="Interviews fetched successfully", data=result)


@router.get("/{interview_id}", response_model=APIResponse[InterviewResponse])
async def get_interview_detail(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
):
    """ទាញយកព័ត៌មានលម្អិត Interview មួយ (ត្រូវជាសមាជិកទើបមើលបាន)"""
    result = await interview_service.get_interview(interview_id, str(current_user["_id"]))
    return APIResponse(success=True, message="Interview fetched successfully", data=result)


@router.patch("/{interview_id}/reschedule", response_model=APIResponse[InterviewResponse])
async def reschedule_interview(
    interview_id: str,
    payload: RescheduleInterviewRequest,
    current_user: dict = Depends(require_employer),
):
    """Employer ប្តូរម៉ោង/ថ្ងៃសម្ភាសន៍ (មានតែ Employer ដែលបានណាត់ដើមទេ ទើបប្តូរបាន)"""
    result = await interview_service.reschedule_interview(interview_id, str(current_user["_id"]), payload)
    return APIResponse(success=True, message="Interview rescheduled successfully", data=result)


@router.post("/{interview_id}/cancel", response_model=APIResponse[InterviewResponse])
async def cancel_interview(
    interview_id: str,
    payload: CancelInterviewRequest,
    current_user: dict = Depends(get_current_user),
):
    """ភាគីណាមួយ (Seeker ឬ Employer) អាចលុបចោល Interview បាន"""
    result = await interview_service.cancel_interview(interview_id, str(current_user["_id"]), payload.reason)
    return APIResponse(success=True, message="Interview cancelled successfully", data=result)


@router.post("/{interview_id}/join", response_model=APIResponse[JoinInterviewResponse])
async def join_interview(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    ត្រូវហៅមុននឹងបើក Video Call — ត្រឡប់ Jitsi Meeting URL ត្រឡប់ទៅឱ្យ App បើក
    (តាម WebView ឬ jitsi_meet SDK)។ អនុញ្ញាតឱ្យចូលបានតែក្នុងកំណត់ពេល (១០ នាទីមុនម៉ោង)
    ហើយប្តូរ Status ទៅ "ongoing" ដោយស្វ័យប្រវត្តិលើកទីមួយដែលភាគីណាមួយចូល។
    """
    result = await interview_service.join_interview(interview_id, current_user)
    return APIResponse(success=True, message="Ready to join interview", data=result)


@router.post("/{interview_id}/complete", response_model=APIResponse[InterviewResponse])
async def complete_interview(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
):
    """ភាគីណាមួយសម្គាល់ថា Interview បានចប់ (ឧ. ចុច "End Call" លើ App)"""
    result = await interview_service.complete_interview(interview_id, str(current_user["_id"]))
    return APIResponse(success=True, message="Interview marked as completed", data=result)
