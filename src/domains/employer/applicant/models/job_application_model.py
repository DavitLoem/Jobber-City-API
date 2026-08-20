from datetime import datetime, timezone
from bson import ObjectId

class JobApplicationModel:
    def __init__(
        self,
        job_id: str | ObjectId,
        company_id: str | ObjectId,
        seeker_user_id: str | ObjectId,
        cover_letter: str = "",
        resume_url: str = None,
        resume_filename: str = None,
        status: str = "pending",
        # 🟢 បន្ថែម Parameter ថ្មី
        status_history: list = None,
        interview_schedule: dict = None,
        feedback: str = ""
    ):
        self.job_id = ObjectId(job_id) if isinstance(job_id, str) else job_id
        self.company_id = ObjectId(company_id) if isinstance(company_id, str) else company_id
        self.seeker_user_id = ObjectId(seeker_user_id) if isinstance(seeker_user_id, str) else seeker_user_id
        
        self.cover_letter = cover_letter
        self.resume_url = resume_url
        self.status = status
        
        # 🟢 កំណត់តម្លៃ Default
        now = datetime.now(timezone.utc)
        self.status_history = status_history if status_history is not None else [
            {"status": "pending", "date": now}
        ]
        self.interview_schedule = interview_schedule if interview_schedule is not None else {}
        self.feedback = feedback

    def to_create_dict(self) -> dict:
        """វេចខ្ចប់ទិន្នន័យសម្រាប់ Insert ចូល Database លើកដំបូង"""
        now = datetime.now(timezone.utc)
        data = self.__dict__.copy()
        
        # បន្ថែមម៉ោងដែលដាក់ពាក្យ និងម៉ោងកែប្រែចុងក្រោយ
        data["applied_at"] = now
        data["updated_at"] = now
        
        return data