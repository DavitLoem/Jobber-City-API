from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str  # ឧ. 'new_application', 'status_update'
    related_id: Optional[str] = None # ផ្ទុក Job ID ឬ Application ID
    is_read: bool
    created_at: datetime
    
class UnreadCountResponse(BaseModel):
    count: int

# (ស្រេចចិត្ត) សម្រាប់ប្រើប្រាស់ក្នុង APIResponse List
class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    
class FCMTokenRequest(BaseModel):
    fcm_token: str