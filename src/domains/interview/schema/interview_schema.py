from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class ScheduleInterviewRequest(BaseModel):
    """Employer ប្រើ Schema នេះដើម្បីណាត់សម្ភាសន៍ជាមួយ Seeker ណាមួយ — មិនកំណត់ត្រឹមតែ
    Seeker ដែលធ្លាប់ដាក់ពាក្យទេ (អាចជ្រើសរើសពី "Browse Seekers" ក៏បាន)"""

    seeker_user_id: str = Field(..., description="ID គណនី Seeker ដែលនឹងត្រូវសម្ភាសន៍")
    scheduled_at: datetime = Field(..., description="ថ្ងៃ-ម៉ោង សម្ភាសន៍ (ISO 8601, UTC)")
    duration_minutes: int = Field(30, ge=10, le=180, description="រយៈពេលប៉ាន់ស្មាន (នាទី)")
    job_id: Optional[str] = Field(None, description="ការងារពាក់ព័ន្ធ (មិនចាំបាច់)")
    application_id: Optional[str] = Field(None, description="ពាក្យសុំការងារពាក់ព័ន្ធ (មិនចាំបាច់)")
    notes: Optional[str] = Field(None, max_length=1000, description="របៀបវារៈ ឬចំណាំសម្រាប់ការសម្ភាសន៍")

    @field_validator("scheduled_at")
    @classmethod
    def must_be_future(cls, v: datetime) -> datetime:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        compare = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if compare <= now:
            raise ValueError("scheduled_at must be in the future.")
        return v


class RescheduleInterviewRequest(BaseModel):
    scheduled_at: datetime
    duration_minutes: Optional[int] = Field(None, ge=10, le=180)

    @field_validator("scheduled_at")
    @classmethod
    def must_be_future(cls, v: datetime) -> datetime:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        compare = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if compare <= now:
            raise ValueError("scheduled_at must be in the future.")
        return v


class CancelInterviewRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


class InterviewOtherParty(BaseModel):
    user_id: str
    name: str
    avatar_url: Optional[str] = None
    role: str


class InterviewResponse(BaseModel):
    id: str
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    application_id: Optional[str] = None
    other_party: InterviewOtherParty
    scheduled_at: datetime
    duration_minutes: int
    status: Literal["scheduled", "ongoing", "completed", "cancelled", "no_show"]
    notes: Optional[str] = None
    meeting_url: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None
    created_at: datetime


class JoinInterviewResponse(BaseModel):
    meeting_url: str
    room_name: str
    display_name: str
    status: str
