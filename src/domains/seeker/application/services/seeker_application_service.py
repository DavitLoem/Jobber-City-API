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

        # ==========================================
        # 🛡️ Condition 1: Spam Protection (Rate Limiting)
        # ==========================================
        # Calculate the time 24 hours ago
        twenty_four_hours_ago = now - timedelta(days=1)
        
        # Count the number of applications submitted in the last 24 hours
        recent_applications_count = await job_applications_collection.count_documents({
            "seeker_user_id": seeker_oid,
            "applied_at": {"$gte": twenty_four_hours_ago}
        })
        
        if recent_applications_count >= DAILY_APPLICATION_LIMIT:
            raise HTTPException(
                status_code=429, # 429: Too Many Requests
                detail=f"You have reached the daily application limit! (Maximum {DAILY_APPLICATION_LIMIT} applications/day). Please try again tomorrow."
            )

        # ==========================================
        # 🛡️ Condition 2: Check Job Status
        # ==========================================
        job = await job_posts_collection.find_one({"_id": job_oid, "status": "active"})
        if not job:
            raise HTTPException(status_code=404, detail="This job is not found or has closed for applications.")

        # ==========================================
        # 🛡️ Condition 3: Profile and CV Requirement
        # ==========================================
        seeker_profile = await seeker_profiles_collection.find_one({"user_id": seeker_oid})
        if not seeker_profile:
            raise HTTPException(status_code=403, detail="You must create a profile before you can apply for a job.")

        # Use the new CV if uploaded during application, otherwise use the one from the profile
        final_resume_url = payload.resume_url or seeker_profile.get("resume_url")
        
        if not final_resume_url:
            raise HTTPException(
                status_code=400, 
                detail="CV/Resume is required! Please provide a CV link or upload one to your profile."
            )

        # ==========================================
        # 🛡️ Condition 4: Prevent Duplicate Applications
        # ==========================================
        existing_app = await job_applications_collection.find_one({
            "job_id": job_oid, 
            "seeker_user_id": seeker_oid
        })
        if existing_app:
            raise HTTPException(status_code=400, detail="You have already applied for this job.")

        # ==========================================
        # ✅ Insert Application Data
        # ==========================================
        application_data = {
            "job_id": job_oid,
            "company_id": job["company_id"], # Link to the company for easy querying by the employer
            "seeker_user_id": seeker_oid,
            "cover_letter": payload.cover_letter or "",
            "resume_url": final_resume_url,
            "status": "pending", # Default status
            "applied_at": now,
            "updated_at": now
        }
        
        await job_applications_collection.insert_one(application_data)
        
        # 📊 Update Analytics (applicant count) for the job post
        await job_posts_collection.update_one(
            {"_id": job_oid}, 
            {"$inc": {"applicant_count": 1}}
        )

        return {
            "success": True, 
            "message": "Application submitted successfully!",
            "remaining_quota": DAILY_APPLICATION_LIMIT - (recent_applications_count + 1) # Inform the remaining quota
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