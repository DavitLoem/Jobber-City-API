from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta

from src.core.mongo import (
    job_posts_collection, 
    seeker_profiles_collection, 
    job_applications_collection,
    company_profiles_collection
    
)
from src.domains.employer.applicant.schemas.job_application_schema import ApplyJobRequest

# 🎯 Set the maximum number of applications a seeker can submit per day (24 hours)
DAILY_APPLICATION_LIMIT = 10 

class SeekerApplicationService:

    async def apply_for_job(self, seeker_user_id: str, job_id: str, payload: ApplyJobRequest) -> dict:
        seeker_oid = ObjectId(seeker_user_id)
        job_oid = ObjectId(job_id)
        now = datetime.now(timezone.utc)

        # 🛡️ លក្ខខណ្ឌទាំង ៤ រក្សាទុកដូចដើម
        twenty_four_hours_ago = now - timedelta(days=1)
        recent_applications_count = await job_applications_collection.count_documents({
            "seeker_user_id": seeker_oid,
            "applied_at": {"$gte": twenty_four_hours_ago}
        })
        
        if recent_applications_count >= DAILY_APPLICATION_LIMIT:
            raise HTTPException(status_code=429, detail=f"You have reached the daily application limit! (Maximum {DAILY_APPLICATION_LIMIT} applications/day). Please try again tomorrow.")

        job = await job_posts_collection.find_one({"_id": job_oid, "status": "active"})
        if not job:
            raise HTTPException(status_code=404, detail="This job is not found or has closed for applications.")

        seeker_profile = await seeker_profiles_collection.find_one({"user_id": seeker_oid})
        if not seeker_profile:
            raise HTTPException(status_code=403, detail="You must create a profile before you can apply for a job.")

        final_resume_url = payload.resume_url or seeker_profile.get("resume_url")
        if not final_resume_url:
            raise HTTPException(status_code=400, detail="CV/Resume is required! Please provide a CV link or upload one to your profile.")

        existing_app = await job_applications_collection.find_one({
            "job_id": job_oid, 
            "seeker_user_id": seeker_oid
        })
        if existing_app:
            raise HTTPException(status_code=400, detail="You have already applied for this job.")

        # ==========================================
        # ✅ ការកែសម្រួល៖ បញ្ចូល Field ថ្មីៗសម្រាប់ Application Detail
        # ==========================================
        application_data = {
            "job_id": job_oid,
            "company_id": job["company_id"],
            "seeker_user_id": seeker_oid,
            "cover_letter": payload.cover_letter or "",
            "resume_url": final_resume_url,

            "status": "pending",
            
            # 🟢 ថែម Field ថ្មីទាំង ៣ នេះដើម្បីកុំឱ្យ Error ពេលទាញមើល Detail
            "status_history": [{"status": "pending", "date": now}], 
            "interview_schedule": {}, 
            "feedback": "", 
            
            "applied_at": now,
            "updated_at": now
        }
        
        await job_applications_collection.insert_one(application_data)
        
        await job_posts_collection.update_one(
            {"_id": job_oid}, 
            {"$inc": {"applicant_count": 1}}
        )

        return {
            "success": True, 
            "message": "Application submitted successfully!",
            "remaining_quota": DAILY_APPLICATION_LIMIT - (recent_applications_count + 1)
        }

    # ==========================================
    # 🎯 Additional feature for Seeker: View own application history
    # ==========================================
    async def get_my_applications(self, seeker_user_id: str, page: int = 1, limit: int = 10) -> list:
        """Allows a seeker to see which companies they have applied to and the status of their applications."""
        
        skip = (page - 1) * limit
        seeker_oid = ObjectId(seeker_user_id)
        
        # We use Aggregation to join with Job Post and Company Profile for a clean presentation
        pipeline = [
            {"$match": {"seeker_user_id": seeker_oid}},
            {"$sort": {"applied_at": -1}},
            {"$skip": skip},
            {"$limit": limit},
            
            # Join to get Job information
            {
                "$lookup": {
                    "from": job_posts_collection.name,
                    "localField": "job_id",
                    "foreignField": "_id",
                    "as": "job_info"
                }
            },
            {"$unwind": {"path": "$job_info", "preserveNullAndEmptyArrays": True}},
            
            # Join to get company name and logo
            {
                "$lookup": {
                    "from": company_profiles_collection.name,
                    "localField": "company_id",
                    "foreignField": "_id",
                    "as": "company_info"
                }
            },
            {"$unwind": {"path": "$company_info", "preserveNullAndEmptyArrays": True}}
        ]
        
        cursor = job_applications_collection.aggregate(pipeline)
        
        results = []
        async for app in cursor:
            job = app.get("job_info", {})
            company = app.get("company_info", {})
            
            results.append({
                "application_id": str(app["_id"]),
                "job_id": str(app["job_id"]),
                "job_title": job.get("title", "Unknown Job"),
                "company_name": company.get("company_name", "Unknown Company"),
                "company_logo": company.get("logo_url"),
                "status": app.get("status"), # pending, reviewed, shortlisted...
                "applied_at": app.get("applied_at")
            })
            
        return results
    
    async def get_application_detail(self, seeker_user_id: str, application_id: str) -> dict:
        seeker_oid = ObjectId(seeker_user_id)
        app_oid = ObjectId(application_id)
        
        pipeline = [
            {"$match": {"_id": app_oid, "seeker_user_id": seeker_oid}},
            {
                "$lookup": {
                    "from": job_posts_collection.name,
                    "localField": "job_id",
                    "foreignField": "_id",
                    "as": "job_info"
                }
            },
            {"$unwind": {"path": "$job_info", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": company_profiles_collection.name,
                    "localField": "company_id",
                    "foreignField": "_id",
                    "as": "company_info"
                }
            },
            {"$unwind": {"path": "$company_info", "preserveNullAndEmptyArrays": True}}
        ]
        
        cursor = job_applications_collection.aggregate(pipeline)
        app_list = await cursor.to_list(length=1)
        
        if not app_list:
            raise HTTPException(status_code=404, detail="Application not found.")
            
        app = app_list[0]
        job = app.get("job_info", {})
        company = app.get("company_info", {})
        
        return {
            "application_id": str(app["_id"]),
            "job_id": str(app["job_id"]),
            "company_id": str(app["company_id"]),
            "job_title": job.get("title", "Unknown Job"),
            "company_name": company.get("company_name", "Unknown Company"),
            "company_logo": company.get("logo_url"),
            
            # 🟢 បញ្ចូល Field លម្អិត
            "cover_letter": app.get("cover_letter"),
            "resume_url": app.get("resume_url"),
            "status": app.get("status"),
            "status_history": app.get("status_history", []),
            "interview_schedule": app.get("interview_schedule"),
            "feedback": app.get("feedback"),
            "applied_at": app.get("applied_at"),
            "updated_at": app.get("updated_at")
        }