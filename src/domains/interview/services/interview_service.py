from datetime import datetime, timezone, timedelta
from typing import Optional
from bson import ObjectId
from fastapi import HTTPException

from src.core.mongo import (
    interviews_collection,
    users_collection,
    seeker_profiles_collection,
    company_profiles_collection,
    job_posts_collection,
    job_applications_collection,
    device_tokens_collection,
)
from src.domains.interview.models.interview_model import InterviewModel, build_meeting_url
from src.domains.chat.services.push_service import send_chat_push_notification

# 🎯 អនុញ្ញាតឱ្យចូលរួម Call បាន ១០ នាទីមុនម៉ោងកំណត់ (កុំឱ្យតឹងពេកសម្រាប់អ្នកមកមុន
# ប៉ុន្តែនៅតែការពារកុំឱ្យចូល Room ឆាប់ពេក ព្រោះ Public Jitsi Server មិនចាំបាច់ "Waiting Room")
JOIN_WINDOW_MINUTES_BEFORE = 10


class InterviewService:

    # ==========================================
    # 🎯 Helpers (Private)
    # ==========================================

    async def _get_display_info(self, user_id: ObjectId, role: str) -> dict:
        user = await users_collection.find_one({"_id": user_id})
        if not user:
            return {"user_id": str(user_id), "name": "Unknown User", "avatar_url": None, "role": role}

        name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get("email", "User")
        avatar_url = user.get("avatar_url")

        if role == "employer":
            company = await company_profiles_collection.find_one({"user_id": user_id})
            if company:
                name = company.get("company_name", name)
                avatar_url = company.get("logo_url", avatar_url)
        elif role == "seeker":
            seeker = await seeker_profiles_collection.find_one({"user_id": user_id})
            if seeker and seeker.get("profile_image_url"):
                avatar_url = seeker.get("profile_image_url")

        return {"user_id": str(user_id), "name": name, "avatar_url": avatar_url, "role": role}

    def _ensure_aware(self, dt: datetime) -> datetime:
        """MongoDB (PyMongo/Motor) ត្រឡប់ Datetime ជា Naive UTC តាមលំនាំដើម — ត្រូវ
        ភ្ជាប់ Timezone ដដែលមុននឹង Compare ជាមួយ datetime.now(timezone.utc)"""
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    async def _format_interview(self, doc: dict, current_user_id: str) -> dict:
        is_seeker_viewing = str(doc["seeker_id"]) == current_user_id
        other_id = doc["employer_id"] if is_seeker_viewing else doc["seeker_id"]
        other_role = "employer" if is_seeker_viewing else "seeker"
        other_party = await self._get_display_info(other_id, other_role)

        job_title = None
        if doc.get("job_id"):
            job = await job_posts_collection.find_one({"_id": doc["job_id"]})
            if job:
                job_title = job.get("title")

        return {
            "id": str(doc["_id"]),
            "job_id": str(doc["job_id"]) if doc.get("job_id") else None,
            "job_title": job_title,
            "application_id": str(doc["application_id"]) if doc.get("application_id") else None,
            "other_party": other_party,
            "scheduled_at": self._ensure_aware(doc["scheduled_at"]),
            "duration_minutes": doc.get("duration_minutes", 30),
            "status": doc.get("status", "scheduled"),
            "notes": doc.get("notes"),
            "meeting_url": build_meeting_url(doc["room_name"]),
            "started_at": self._ensure_aware(doc["started_at"]) if doc.get("started_at") else None,
            "ended_at": self._ensure_aware(doc["ended_at"]) if doc.get("ended_at") else None,
            "cancel_reason": doc.get("cancel_reason"),
            "created_at": self._ensure_aware(doc["created_at"]),
        }

    async def _assert_participant(self, interview_id: str, user_id: str) -> dict:
        if not ObjectId.is_valid(interview_id):
            raise HTTPException(status_code=400, detail="Invalid interview ID.")

        doc = await interviews_collection.find_one({"_id": ObjectId(interview_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Interview not found.")

        if user_id not in [str(p) for p in doc["participant_ids"]]:
            raise HTTPException(status_code=403, detail="You are not a participant of this interview.")

        return doc

    async def _notify(self, recipient_id: ObjectId, title: str, body: str, data: dict) -> None:
        """ការពារកុំឱ្យ Push Notification បរាជ័យធ្វើឱ្យ Action ចម្បង (Schedule/Cancel) បរាជ័យតាម"""
        try:
            tokens_cursor = device_tokens_collection.find({"user_id": recipient_id})
            tokens = [t["fcm_token"] async for t in tokens_cursor]
            if not tokens:
                return
            await send_chat_push_notification(fcm_tokens=tokens, title=title, body=body, data=data)
        except Exception:
            pass

    # ==========================================
    # 🎯 Schedule (Employer only)
    # ==========================================

    async def schedule_interview(self, employer_user: dict, payload) -> dict:
        employer_id = employer_user["_id"]
        company = await company_profiles_collection.find_one({"user_id": employer_id})
        if not company:
            raise HTTPException(status_code=403, detail="You need a company profile before scheduling interviews.")

        if not ObjectId.is_valid(payload.seeker_user_id):
            raise HTTPException(status_code=400, detail="Invalid seeker ID.")
        seeker_oid = ObjectId(payload.seeker_user_id)

        seeker_user = await users_collection.find_one({"_id": seeker_oid})
        if not seeker_user or seeker_user.get("role") != "seeker":
            raise HTTPException(status_code=404, detail="Seeker not found.")

        job_oid = None
        if payload.job_id:
            if not ObjectId.is_valid(payload.job_id):
                raise HTTPException(status_code=400, detail="Invalid job ID.")
            job_oid = ObjectId(payload.job_id)
            job = await job_posts_collection.find_one({"_id": job_oid, "company_id": company["_id"]})
            if not job:
                raise HTTPException(status_code=404, detail="Job not found or it does not belong to you.")

        application_oid = None
        if payload.application_id:
            if not ObjectId.is_valid(payload.application_id):
                raise HTTPException(status_code=400, detail="Invalid application ID.")
            application_oid = ObjectId(payload.application_id)
            application = await job_applications_collection.find_one({
                "_id": application_oid,
                "company_id": company["_id"],
            })
            if not application:
                raise HTTPException(status_code=404, detail="Application not found or it does not belong to you.")
            if application.get("seeker_user_id") != seeker_oid:
                raise HTTPException(status_code=400, detail="This application does not belong to the specified seeker.")

        model = InterviewModel(
            employer_id=employer_id,
            seeker_id=seeker_oid,
            company_id=company["_id"],
            scheduled_at=payload.scheduled_at,
            duration_minutes=payload.duration_minutes,
            job_id=job_oid,
            application_id=application_oid,
            notes=payload.notes,
        )
        new_doc = model.to_create_dict()
        await interviews_collection.insert_one(new_doc)

        await self._notify(
            recipient_id=seeker_oid,
            title="New interview scheduled",
            body=f"You have an interview on {payload.scheduled_at.strftime('%b %d, %Y at %H:%M UTC')}.",
            data={"type": "interview_scheduled", "interview_id": str(new_doc["_id"])},
        )

        return await self._format_interview(new_doc, str(employer_id))

    # ==========================================
    # 🎯 List / Get
    # ==========================================

    async def list_interviews(
        self, user_id: str, status_filter: Optional[str] = None, page: int = 1, limit: int = 20
    ) -> list:
        query: dict = {"participant_ids": ObjectId(user_id)}
        if status_filter and status_filter != "all":
            query["status"] = status_filter

        skip = (page - 1) * limit
        # 🎯 តម្រៀបតាមម៉ោងណាត់ជិតបំផុតមុន (មិនមែនតាមកាលបង្កើតដូច Chat ទេ — Interview
        # ដែលនឹងមកដល់ឆាប់បំផុតគួរតែឡើងលើគេនៅលើ App)
        cursor = interviews_collection.find(query).sort("scheduled_at", 1).skip(skip).limit(limit)

        results = []
        async for doc in cursor:
            results.append(await self._format_interview(doc, user_id))
        return results

    async def get_interview(self, interview_id: str, user_id: str) -> dict:
        doc = await self._assert_participant(interview_id, user_id)
        return await self._format_interview(doc, user_id)

    # ==========================================
    # 🎯 Reschedule (Employer only — they own the scheduling)
    # ==========================================

    async def reschedule_interview(self, interview_id: str, employer_user_id: str, payload) -> dict:
        doc = await self._assert_participant(interview_id, employer_user_id)
        if str(doc["employer_id"]) != employer_user_id:
            raise HTTPException(status_code=403, detail="Only the employer who scheduled this interview can reschedule it.")
        if doc["status"] in ["completed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot reschedule a {doc['status']} interview.")

        now = datetime.now(timezone.utc)
        update: dict = {"scheduled_at": payload.scheduled_at, "status": "scheduled", "updated_at": now}
        if payload.duration_minutes:
            update["duration_minutes"] = payload.duration_minutes

        updated = await interviews_collection.find_one_and_update(
            {"_id": doc["_id"]}, {"$set": update}, return_document=True
        )

        await self._notify(
            recipient_id=doc["seeker_id"],
            title="Interview rescheduled",
            body=f"Your interview was moved to {payload.scheduled_at.strftime('%b %d, %Y at %H:%M UTC')}.",
            data={"type": "interview_rescheduled", "interview_id": interview_id},
        )
        return await self._format_interview(updated, employer_user_id)

    # ==========================================
    # 🎯 Cancel (either participant can cancel)
    # ==========================================

    async def cancel_interview(self, interview_id: str, user_id: str, reason: Optional[str]) -> dict:
        doc = await self._assert_participant(interview_id, user_id)
        if doc["status"] in ["completed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel a {doc['status']} interview.")

        updated = await interviews_collection.find_one_and_update(
            {"_id": doc["_id"]},
            {"$set": {
                "status": "cancelled",
                "cancelled_by": ObjectId(user_id),
                "cancel_reason": reason,
                "updated_at": datetime.now(timezone.utc),
            }},
            return_document=True,
        )

        other_id = doc["employer_id"] if str(doc["seeker_id"]) == user_id else doc["seeker_id"]
        await self._notify(
            recipient_id=other_id,
            title="Interview cancelled",
            body=reason or "The interview has been cancelled.",
            data={"type": "interview_cancelled", "interview_id": interview_id},
        )
        return await self._format_interview(updated, user_id)

    # ==========================================
    # 🎯 Join (either participant — returns the Jitsi room to open)
    # ==========================================

    async def join_interview(self, interview_id: str, current_user: dict) -> dict:
        user_id = str(current_user["_id"])
        doc = await self._assert_participant(interview_id, user_id)

        if doc["status"] == "cancelled":
            raise HTTPException(status_code=400, detail="This interview has been cancelled.")
        if doc["status"] == "completed":
            raise HTTPException(status_code=400, detail="This interview has already ended.")

        now = datetime.now(timezone.utc)
        scheduled_at = self._ensure_aware(doc["scheduled_at"])
        window_open_at = scheduled_at - timedelta(minutes=JOIN_WINDOW_MINUTES_BEFORE)

        if now < window_open_at:
            minutes_left = int((window_open_at - now).total_seconds() // 60) + 1
            raise HTTPException(
                status_code=400,
                detail=(
                    f"This interview hasn't started yet. You can join {JOIN_WINDOW_MINUTES_BEFORE} minutes "
                    f"before the scheduled time — about {minutes_left} more minute(s)."
                ),
            )

        new_status = doc["status"]
        update: dict = {"updated_at": now}
        if doc["status"] == "scheduled":
            update["status"] = "ongoing"
            update["started_at"] = now
            new_status = "ongoing"

        await interviews_collection.update_one({"_id": doc["_id"]}, {"$set": update})

        role = "employer" if str(doc["employer_id"]) == user_id else "seeker"
        display_info = await self._get_display_info(current_user["_id"], role)

        return {
            "meeting_url": build_meeting_url(doc["room_name"]),
            "room_name": doc["room_name"],
            "display_name": display_info["name"],
            "status": new_status,
        }

    # ==========================================
    # 🎯 Complete (either participant can mark it done)
    # ==========================================

    async def complete_interview(self, interview_id: str, user_id: str) -> dict:
        doc = await self._assert_participant(interview_id, user_id)
        if doc["status"] in ["completed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Interview is already {doc['status']}.")

        now = datetime.now(timezone.utc)
        updated = await interviews_collection.find_one_and_update(
            {"_id": doc["_id"]},
            {"$set": {"status": "completed", "ended_at": now, "updated_at": now}},
            return_document=True,
        )
        return await self._format_interview(updated, user_id)


interview_service = InterviewService()
