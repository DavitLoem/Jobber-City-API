from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from src.core.response import APIResponse

from src.domains.chat.schema.chat_schema import (
    StartConversationRequest,
    MessageSendRequest,
    DeviceTokenRegister,
    DeviceTokenRemove,
    ConversationResponse,
    MessageHistoryResponse,
    MessageResponse,
)
from src.domains.chat.services.chat_service import chat_service
from src.dependencies.dependencies import get_current_user, require_mobile_users

# 🎯 មានតែ Seeker & Employer ទេ ដែលចូលប្រើ Chat Feature នេះបាន (Admin មិនចូលរួម Chat)
router = APIRouter(
    prefix="/api/chat",
    tags=["Mobile - Chat"],
    dependencies=[Depends(require_mobile_users)],
)


@router.post("/conversations", response_model=APIResponse[ConversationResponse])
async def start_conversation(
    payload: StartConversationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    បង្កើត ឬ ទាញយក Conversation ដែលមានស្រាប់រវាង User បច្ចុប្បន្ន និងភាគីម្ខាងទៀត។
    ប្រើ Route នេះនៅពីក្រោយប៊ូតុង "Message" លើ Job Post ឬ Applicant Profile
    (Flutter គួរហៅ Route នេះមុន រួចយក `id` ដែលបានមកបើក Chat Screen)។
    """
    result = await chat_service.get_or_create_conversation(
        current_user=current_user,
        other_user_id=payload.other_user_id,
        job_id=payload.job_id,
    )
    return APIResponse(success=True, message="Conversation ready", data=result)


@router.get("/conversations", response_model=APIResponse[List[ConversationResponse]])
async def list_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """ទាញយកបញ្ជី Chat ទាំងអស់របស់ User (រៀបតាម Message ចុងក្រោយ ដូច WhatsApp/Messenger)"""
    result = await chat_service.list_conversations(str(current_user["_id"]), page, limit)
    return APIResponse(success=True, message="Conversations fetched successfully", data=result)


@router.get("/conversations/{conversation_id}/messages", response_model=APIResponse[MessageHistoryResponse])
async def get_messages(
    conversation_id: str,
    before: Optional[str] = Query(None, description="Message ID ចាស់បំផុតដែលទើប Load រួច (សម្រាប់ Infinite Scroll Load More)"),
    limit: int = Query(30, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """ទាញយកប្រវត្តិសារ (Cursor-based Pagination - Load ថ្មីៗមុន រួច Scroll Up ដើម្បី Load ចាស់ជាងនេះ)"""
    result = await chat_service.get_messages(conversation_id, str(current_user["_id"]), before, limit)
    return APIResponse(success=True, message="Messages fetched successfully", data=result)


@router.post("/conversations/{conversation_id}/read", response_model=APIResponse)
async def mark_conversation_read(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """សម្គាល់ថា Conversation នេះត្រូវបានអានរួច (កំណត់ Unread Count = 0 + ផ្ញើ Read Receipt ទៅភាគីម្ខាងទៀត)"""
    await chat_service.mark_as_read(conversation_id, str(current_user["_id"]))
    return APIResponse(success=True, message="Conversation marked as read")


@router.post("/conversations/{conversation_id}/messages", response_model=APIResponse[MessageResponse])
async def send_message_via_rest(
    conversation_id: str,
    payload: MessageSendRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    🎯 Fallback ផ្ញើសារតាម REST (មិនតម្រូវឱ្យ Connect WebSocket ជានិច្ចទេ)។
    សូម Recommend ប្រើ WebSocket (/api/chat/ws) សម្រាប់ពេល Chat Screen កំពុងបើក
    ព្រោះលឿន និង Real-time ជាង ប៉ុន្តែ Route នេះមានប្រយោជន៍ជា Fallback ពេល
    WebSocket Connection មិនល្អ ឬចង់ផ្ញើសារពេលមិនទាន់បាន Connect។
    """
    result = await chat_service.send_message(
        conversation_id=conversation_id,
        sender=current_user,
        content=payload.content,
        message_type=payload.message_type,
        attachment_url=payload.attachment_url,
        client_temp_id=payload.client_temp_id,
    )
    return APIResponse(success=True, message="Message sent successfully", data=result)


@router.post("/device-tokens", response_model=APIResponse)
async def register_device_token(
    payload: DeviceTokenRegister,
    current_user: dict = Depends(get_current_user),
):
    """
    ចុះឈ្មោះ FCM Device Token ដើម្បីទទួល Push Notification ពេលមាន Message ថ្មី
    ខណៈកម្មវិធីបិទ ឬនៅ Background។ Flutter គួរហៅ Route នេះរាល់ពេល Login ជោគជ័យ
    (ក៏ដូចជារាល់ពេល Firebase ចេញ Token ថ្មីតាម onTokenRefresh)។
    """
    await chat_service.register_device_token(str(current_user["_id"]), payload.fcm_token, payload.platform)
    return APIResponse(success=True, message="Device token registered")


@router.delete("/device-tokens", response_model=APIResponse)
async def remove_device_token(
    payload: DeviceTokenRemove,
    current_user: dict = Depends(get_current_user),
):
    """លុប Device Token ចោល (គួរហៅពេល Logout ដើម្បីកុំឱ្យ Device នេះបន្តទទួល Notification)"""
    await chat_service.remove_device_token(payload.fcm_token)
    return APIResponse(success=True, message="Device token removed")
