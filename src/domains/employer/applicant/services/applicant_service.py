from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime, timezone

from src.core.mongo import (
    job_posts_collection, 
    seeker_profiles_collection, 
    job_applications_collection, 
    company_profiles_collection,
    users_collection
)
from src.domains.profile.seeker_profile.services.core_profile_service import helper_format_profile

class ApplicantService:

    async def get_applicants_by_job(self, employer_user_id: str, job_id: str, status_filter: str = "all") -> list:
        query = {}

        # ១. ការពារសុវត្ថិភាព
        employer_profile = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)})
        if not employer_profile:
            raise HTTPException(status_code=403, detail="Employer profile not found.")
            
        company_id = employer_profile["_id"]

        # ២. ឆែកមើល All Jobs
        if job_id.lower() == "all":
            query["company_id"] = company_id
        else:
            if not ObjectId.is_valid(job_id):
                raise HTTPException(status_code=400, detail="Invalid Job ID format.")
                
            query["job_id"] = ObjectId(job_id)
            query["company_id"] = company_id

        # ៣. ត្រងតាម Status
        if status_filter and status_filter.lower() != "all":
            query["status"] = status_filter.lower()

        # ៤. Pipeline Join 
        pipeline = [
            {"$match": query},
            {"$sort": {"applied_at": -1}},
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
                    "from": seeker_profiles_collection.name,
                    "localField": "seeker_user_id",
                    "foreignField": "user_id",
                    "as": "seeker_info"
                }
            },
            {"$unwind": {"path": "$seeker_info", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": users_collection.name,
                    "localField": "seeker_user_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}}
        ]
        
        cursor = job_applications_collection.aggregate(pipeline)
        
        applicants = []
        async for app in cursor:
            seeker = app.get("seeker_info", {})
            user = app.get("user_info", {}) 
            job = app.get("job_info", {})
            
            applicants.append({
                "application_id": str(app["_id"]),
                "seeker_user_id": str(app["seeker_user_id"]),
                "job_title": job.get("title", "Unknown Job"),
                "first_name": user.get("first_name", "Unknown"),
                "last_name": user.get("last_name", ""),
                "profile_image_url": seeker.get("profile_image_url"),
                "current_position": seeker.get("current_position", ""),
                "skills": seeker.get("skills", []), 
                "years_of_experience": seeker.get("years_of_experience", 0), 
                "resume_url": app.get("resume_url"),
                "resume_filename": app.get("resume_filename"),
                "cover_letter": app.get("cover_letter"),
                "status": app.get("status"),
                "interview_schedule": app.get("interview_schedule"),
                "feedback": app.get("feedback"),
                "applied_at": app.get("applied_at")
            })
            
        return applicants
    
    async def get_employer_job_dropdown_list(self, employer_user_id: str) -> list:
        """
        ទាញយកបញ្ជីការងាររបស់ Employer សម្រាប់បង្ហាញក្នុង Dropdown
        ជាមួយនឹង Smart Labeling និងការតម្រៀប Status (Active មុន)
        """
        # ១. ផ្ទៀងផ្ទាត់ Employer Profile
        employer_profile = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)})
        if not employer_profile:
            raise HTTPException(status_code=403, detail="Employer profile not found.")
            
        company_id = employer_profile["_id"]

        # ២. ទាញយកការងារ ដោយយកតែ Field ចាំបាច់ ដើម្បីឱ្យលឿន
        cursor = job_posts_collection.find(
            {"company_id": company_id},
            {"title": 1, "work_type": 1, "created_at": 1, "status": 1}
        ).sort([
            ("status", 1), # តម្រៀប 'active' មុន 'closed' 
            ("created_at", -1) # ការងារថ្មីៗនៅខាងលើ
        ])
        
        dropdown_jobs = []
        async for job in cursor:
            title = job.get("title", "Unknown Job")
            work_type = job.get("work_type", "").capitalize()
            created_at = job.get("created_at")
            status = job.get("status", "active")
            
            # ៣. Smart Labeling Logic
            # Format ថ្ងៃខែ ឧទាហរណ៍: Aug 2026
            date_str = created_at.strftime("%b %Y") if created_at else ""
            
            # ផ្គុំឈ្មោះបញ្ជូលគ្នា
            display_name = title
            if work_type:
                display_name += f" ({work_type})"
            if date_str:
                display_name += f" - {date_str}"
                
            # បន្ថែមសញ្ញាសម្គាល់បើការងារនោះបិទហើយ
            if status != "active":
                display_name += " [Closed]"

            dropdown_jobs.append({
                "job_id": str(job["_id"]),
                "display_name": display_name,
                "status": status
            })
            
        return dropdown_jobs

    async def update_applicant_status(self, employer_user_id: str, application_id: str, new_status: str, interview_schedule: dict = None, feedback: str = None) -> dict:
        """ផ្លាស់ប្តូរស្ថានភាពបេក្ខជន (ឧ. ហៅមកសម្ភាសន៍ ឬបដិសេធ)"""
        
        # កំណត់ Status ដែលអនុញ្ញាតឱ្យប្រើប្រាស់បាន
        valid_statuses = ["pending", "reviewed", "shortlisted", "interview", "hired", "rejected"] 
        if new_status not in valid_statuses:
             raise HTTPException(status_code=400, detail="Status is not valid.") 

        company = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)}) 
        if not company:
             raise HTTPException(status_code=403, detail="Permission Denied") 
             
        now = datetime.now(timezone.utc)
        
        # 🟢 បង្កើត Data សម្រាប់ Update
        update_data = {
            "status": new_status, 
            "updated_at": now
        }
        
        # 🟢 បញ្ចូល Interview Schedule និង Feedback (ប្រសិនបើមាន)
        if new_status == "interview" and interview_schedule:
             update_data["interview_schedule"] = interview_schedule
        if feedback:
             update_data["feedback"] = feedback

        # ធ្វើការ Update ដោយប្រាកដថា Application នោះ ដាក់មកកាន់ Company នេះមែន (ការពារ Employer ផ្សេងមកកែ) 
        updated_app = await job_applications_collection.find_one_and_update(
            {
                "_id": ObjectId(application_id), 
                "company_id": company["_id"] 
            },
            {
                "$set": update_data,
                "$push": {"status_history": {"status": new_status, "date": now}} # 🟢 Push ប្រវត្តិថ្មីចូល Array
            },
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