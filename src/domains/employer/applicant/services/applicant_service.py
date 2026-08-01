from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime, timezone

from src.core.mongo import (
    job_posts_collection, 
    seeker_profiles_collection, 
    job_applications_collection, 
    company_profiles_collection
)
from src.domains.profile.seeker_profile.services.core_profile_service import helper_format_profile

class ApplicantService:

    async def get_applicants_by_job(self, employer_user_id: str, job_id: str, status_filter: str = "all") -> list:
        """ទាញយកបញ្ជីអ្នកដាក់ពាក្យ ដោយចាត់ថ្នាក់តាម Job នីមួយៗ"""
        
        # ១. ឆែកមើល Company របស់ Employer
        company = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)})
        if not company:
            raise HTTPException(status_code=403, detail="company profile not found for this employer.")

        # ២. ឆែកមើល Job ថាជារបស់ក្រុមហ៊ុនគាត់ពិតមែនឬអត់ (សុវត្ថិភាពទិន្នន័យ)
        job = await job_posts_collection.find_one({
            "_id": ObjectId(job_id), 
            "company_id": company["_id"]
        })
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or it does not belong to you.")

        # ៣. រៀបចំ Query សម្រាប់ទាញយក (ដោយមាន Filter តាម Status)
        query = {"job_id": ObjectId(job_id)}
        if status_filter and status_filter.lower() != "all":
            query["status"] = status_filter.lower()

        # ៤. Join ទិន្នន័យ Application ជាមួយ Seeker Profile
        pipeline = [
            {"$match": query},
            {"$sort": {"applied_at": -1}}, # យកអ្នកដាក់ពាក្យថ្មីៗមកមុនគេ
            {
                "$lookup": {
                    "from": seeker_profiles_collection.name,
                    "localField": "seeker_user_id",
                    "foreignField": "user_id",
                    "as": "seeker_info"
                }
            },
            # ប្រើ preserveNullAndEmptyArrays ដើម្បីកុំឱ្យបាត់ទិន្នន័យ ទោះ Seeker លុប Profile ក៏ដោយ
            {"$unwind": {"path": "$seeker_info", "preserveNullAndEmptyArrays": True}}
        ]
        
        cursor = job_applications_collection.aggregate(pipeline)
        
        applicants = []
        async for app in cursor:
            seeker = app.get("seeker_info", {})
            applicants.append({
                "application_id": str(app["_id"]),
                "seeker_user_id": str(app["seeker_user_id"]),
                "first_name": seeker.get("first_name", "Unknown"),
                "last_name": seeker.get("last_name", ""),
                "profile_image_url": seeker.get("profile_image_url"),
                "current_position": seeker.get("current_position", ""),
                
                "skills": seeker.get("skills", []), 
                "years_of_experience": seeker.get("years_of_experience", 0), 
                
                "resume_url": app.get("resume_url"),
                "cover_letter": app.get("cover_letter"),
                "status": app.get("status"),
                "applied_at": app.get("applied_at")
            })
            
        return applicants

    async def update_applicant_status(self, employer_user_id: str, application_id: str, new_status: str) -> dict:
        """ផ្លាស់ប្តូរស្ថានភាពបេក្ខជន (ឧ. ហៅមកសម្ភាសន៍ ឬបដិសេធ)"""
        
        # កំណត់ Status ដែលអនុញ្ញាតឱ្យប្រើប្រាស់បាន
        valid_statuses = ["pending", "reviewed", "shortlisted", "interview", "hired", "rejected"]
        if new_status not in valid_statuses:
             raise HTTPException(status_code=400, detail="Status is not valid.")

        company = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)})
        if not company:
             raise HTTPException(status_code=403, detail="Permission Denied")

        # ធ្វើការ Update ដោយប្រាកដថា Application នោះ ដាក់មកកាន់ Company នេះមែន (ការពារ Employer ផ្សេងមកកែ)
        updated_app = await job_applications_collection.find_one_and_update(
            {
                "_id": ObjectId(application_id), 
                "company_id": company["_id"]
            },
            {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}},
            return_document=True
        )

        if not updated_app:
            raise HTTPException(status_code=404, detail="Application not found or it does not belong to you.")

        return {"application_id": str(updated_app["_id"]), "new_status": new_status}

    async def get_seeker_profile_readonly(self, employer_user_id: str, seeker_user_id: str) -> dict:
        """Employer ចុចមើល Profile ពេញលេញរបស់ Seeker"""
        
        # ឆែកសិទ្ធិថាគាត់ពិតជា Employer មែន
        company = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)})
        if not company:
             raise HTTPException(status_code=403, detail="Permission Denied")

        # ទាញយក Profile ដោយប្រើ Helper របស់ Core Profile ផ្ទាល់តែម្តង
        seeker_profile = await seeker_profiles_collection.find_one({"user_id": ObjectId(seeker_user_id)})
        if not seeker_profile:
            raise HTTPException(status_code=404, detail="Seeker profile not found.")

        return helper_format_profile(seeker_profile)