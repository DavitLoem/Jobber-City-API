from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class StartConversationRequest(BaseModel):
    other_user_id: str = Field(..., description="ID របស់ភាគីម្ខាងទៀត (Seeker ឬ Employer)")
    job_id: Optional[str] = Field(None, description="ID ការងារ ដែលជាប្រធានបទចាប់ផ្តើមសន្ទនា (មិនចាំបាច់ទេ)")


class MessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: Literal["text", "image", "file"] = "text"
    attachment_url: Optional[str] = None
    client_temp_id: Optional[str] = Field(
        None, description="UUID បង្កើតដោយ Client សម្រាប់ Optimistic UI Matching"
    )


class DeviceTokenRegister(BaseModel):
    fcm_token: str
    platform: Literal["android", "ios"] = "android"


class DeviceTokenRemove(BaseModel):
    fcm_token: str


class OtherPartyInfo(BaseModel):
    user_id: str
    name: str
    avatar_url: Optional[str] = None
    role: str
    is_online: bool = False


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    sender_role: str
    message_type: str
    content: str
    attachment_url: Optional[str] = None
    status: str
    client_temp_id: Optional[str] = None
    created_at: datetime


class ConversationResponse(BaseModel):
    id: str
    job_id: Optional[str] = None
    other_party: OtherPartyInfo
    last_message: Optional[str] = None
    last_message_type: Optional[str] = None
    last_message_at: Optional[datetime] = None
    last_sender_id: Optional[str] = None
    unread_count: int = 0
    created_at: datetime


class MessageHistoryResponse(BaseModel):
    messages: List[MessageResponse]
    has_more: bool
