import secrets
from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional


class InterviewModel:
    """
    ១ Interview = ការណាត់សម្ភាសន៍តាម Video Call មួយដង រវាង Employer ១ នាក់ និង
    Seeker ១ នាក់។ ខុសពី Chat Conversation (ដែលមានតែម្តងគត់ក្នុងមួយគូ) — Employer
    អាចណាត់សម្ភាសន៍ច្រើនដងជាមួយ Seeker ដដែល (ឧ. Round 1, Round 2), ដូច្នេះ
    មិនប្រើ Get-or-Create Pattern ទេ គឺបង្កើត Document ថ្មីរាល់ពេល Schedule។

    Video Call ខ្លួនឯងប្រើ Jitsi Meet (meet.jit.si) — មិនចាំបាច់ Signaling Server
    ឬ TURN Server ផ្ទាល់ខ្លួនទេ គ្រាន់តែបង្កើត room_name ដែលទាយមិនចេញ ហើយភាគីទាំង
    ពីរបើក URL ដូចគ្នា Jitsi's SFU នឹងគ្រប់គ្រង Media ទាំងអស់។
    """

    STATUSES = ["scheduled", "ongoing", "completed", "cancelled", "no_show"]

    def __init__(
        self,
        employer_id: str | ObjectId,
        seeker_id: str | ObjectId,
        company_id: str | ObjectId,
        scheduled_at: datetime,
        duration_minutes: int = 30,
        job_id: Optional[str | ObjectId] = None,
        application_id: Optional[str | ObjectId] = None,
        notes: Optional[str] = None,
    ):
        self.employer_id = ObjectId(employer_id) if isinstance(employer_id, str) else employer_id
        self.seeker_id = ObjectId(seeker_id) if isinstance(seeker_id, str) else seeker_id
        self.company_id = ObjectId(company_id) if isinstance(company_id, str) else company_id
        self.job_id = (ObjectId(job_id) if isinstance(job_id, str) else job_id) if job_id else None
        self.application_id = (
            ObjectId(application_id) if isinstance(application_id, str) else application_id
        ) if application_id else None

        # 🎯 Array សម្រាប់ Query លឿន៖ "រកគ្រប់ Interview ដែល User នេះជាសមាជិក"
        # (ដូចគ្នានឹង participant_ids ក្នុង ConversationModel)
        self.participant_ids = [self.seeker_id, self.employer_id]

        # ត្រូវប្រាកដថា scheduled_at មាន Timezone (UTC) ជានិច្ច
        self.scheduled_at = scheduled_at if scheduled_at.tzinfo else scheduled_at.replace(tzinfo=timezone.utc)
        self.duration_minutes = duration_minutes
        self.notes = notes

        self.status = "scheduled"

        # 🎯 Room name មិនទាយបាន (Interview ID + Random Token ២៤ bit ទៀត) ព្រោះ
        # meet.jit.si ជា Public Server — នរណាដឹង Room Name អាចចូលរួមបាន ដូច្នេះ
        # ភាពសុវត្ថិភាពពឹងផ្អែកលើ Room Name ខ្លួនឯងមិនអាចទាយចេញ (មិនមែន Password)
        self.room_name = f"jobbercity-interview-{ObjectId()}-{secrets.token_urlsafe(6)}"

        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        self.cancelled_by: Optional[ObjectId] = None
        self.cancel_reason: Optional[str] = None

    def to_create_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        data = self.__dict__.copy()
        data["_id"] = ObjectId()
        data["created_at"] = now
        data["updated_at"] = now
        return data


def build_meeting_url(room_name: str) -> str:
    """URL ដែល Flutter App បើក (ក្នុង WebView ឬ jitsi_meet SDK) ដើម្បីចូលរួម Call"""
    return f"https://meet.jit.si/{room_name}"
