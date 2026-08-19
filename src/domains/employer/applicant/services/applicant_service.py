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
from src.domains.notification.services.notification_service import notification_service

class ApplicantService:
    
    def _format_applicant_response(self, app: dict) -> dict:
        seeker = app.get("seeker_info", {})
        user = app.get("user_info", {}) 
        job = app.get("job_info", {})
        
        return {
            "application_id": str(app["_id"]),
            "seeker_user_id": str(app["seeker_user_id"]),
            "job_title": job.get("title", "Unknown Job"),
            "first_name": user.get("first_name", "Unknown"),
            "last_name": user.get("last_name", ""),
            "email": user.get("email", ""),           
            "phone": seeker.get("phone_number", ""),  
            "gender": seeker.get("gender", "Unknown"),
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
        }
        
    def _build_applicant_pipeline(
        self, company_id: ObjectId, job_id: str, status_filter: str, 
        search_keyword: str, sort_by: str, skip: int, limit: int, is_export: bool = False
    ) -> list:
        query = {"company_id": company_id}

        if job_id.lower() != "all":
            if ObjectId.is_valid(job_id):
                query["job_id"] = ObjectId(job_id)
                
        if status_filter and status_filter.lower() != "all":
            query["status"] = status_filter.lower()

        # 🟢 ១. ដក {"$sort": {"applied_at": -1}} ចេញពីកន្លែងចាស់សិន 
        pipeline = [
            {"$match": query},
            {"$lookup": {"from": job_posts_collection.name, "localField": "job_id", "foreignField": "_id", "as": "job_info"}},
            {"$unwind": {"path": "$job_info", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": seeker_profiles_collection.name, "localField": "seeker_user_id", "foreignField": "user_id", "as": "seeker_info"}},
            {"$unwind": {"path": "$seeker_info", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": users_collection.name, "localField": "seeker_user_id", "foreignField": "_id", "as": "user_info"}},
            {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}}
        ]
        
        if search_keyword and search_keyword.strip():
            search_regex = {"$regex": search_keyword.strip(), "$options": "i"}
            pipeline.append({
                "$match": {
                    "$or": [
                        {"user_info.first_name": search_regex},
                        {"user_info.last_name": search_regex},
                        {"seeker_info.skills": search_regex}
                    ]
                }
            })
            
        # 🟢 ២. បន្ថែមដំណាក់កាល តម្រៀបទិន្នន័យ (Sorting Stage) នៅទីនេះវិញ
        if sort_by == "name_asc":
            # តម្រៀបតាមឈ្មោះ A-Z
            pipeline.append({"$sort": {"user_info.first_name": 1, "user_info.last_name": 1}})
        elif sort_by == "interview_asc":
            # តម្រៀបតាមថ្ងៃសម្ភាសន៍ជិតបំផុត (អ្នកអត់មានថ្ងៃសម្ភាសន៍នឹងធ្លាក់ទៅក្រោម)
            pipeline.append({"$sort": {"interview_schedule.date": 1, "applied_at": -1}})
        else:
            # លំនាំដើម: តម្រៀបតាមអ្នកដាក់ពាក្យថ្មីៗមុនគេ
            pipeline.append({"$sort": {"applied_at": -1}})

        pipeline.extend([
            {"$skip": skip},
            {"$limit": limit}
        ])
        
        if not is_export:
            pipeline.extend([
                {"$skip": skip},
                {"$limit": limit}
            ])
        
        return pipeline

    # 🟢 ១. បន្ថែម parameter `search_keyword`
    async def get_applicants_by_job(
        self, 
        employer_user_id: str, 
        job_id: str, 
        status_filter: str = "all", 
        search_keyword: str = None,
        sort_by: str = "newest",
        page: int = 1,      
        limit: int = 20,
        is_export: bool = False    
    ) -> list:
        
        # ១. ការពារសុវត្ថិភាព និងទាញយក Company ID
        employer_profile = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)})
        if not employer_profile:
            raise HTTPException(status_code=403, detail="Employer profile not found.")
            
        # ២. កសាង Pipeline ដោយហៅ Helper
        skip = (page - 1) * limit
        pipeline = self._build_applicant_pipeline(
            company_id=employer_profile["_id"],
            job_id=job_id,
            status_filter=status_filter,
            search_keyword=search_keyword,
            sort_by=sort_by,
            skip=skip,
            limit=limit,
            is_export=is_export
        )
        
        # ៣. ប្រតិបត្តិការ Query និងទាញទិន្នន័យ (ហៅ Helper រៀបចំ Format)
        cursor = job_applications_collection.aggregate(pipeline)
        
        applicants = []
        async for app in cursor:
            applicants.append(self._format_applicant_response(app))
            
        return applicants
    
    async def get_application_detail(self, employer_user_id: str, application_id: str) -> dict:
        # ១. ឆែកមើល Company Profile ដើម្បីការពារសុវត្ថិភាព
        employer_profile = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)})
        if not employer_profile:
            raise HTTPException(status_code=403, detail="Employer profile not found.")
            
        if not ObjectId.is_valid(application_id):
            raise HTTPException(status_code=400, detail="Invalid Application ID format.")

        # ២. បង្កើត Pipeline ដើម្បី Join ទិន្នន័យដូចពេលទាញយកបញ្ជីដែរ ប៉ុន្តែយកតែ ១
        pipeline = [
            {
                "$match": {
                    "_id": ObjectId(application_id),
                    "company_id": employer_profile["_id"] # ធានាថា Employer នេះជាម្ចាស់ការងារពិតប្រាកដ
                }
            },
            {"$lookup": {"from": job_posts_collection.name, "localField": "job_id", "foreignField": "_id", "as": "job_info"}},
            {"$unwind": {"path": "$job_info", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": seeker_profiles_collection.name, "localField": "seeker_user_id", "foreignField": "user_id", "as": "seeker_info"}},
            {"$unwind": {"path": "$seeker_info", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": users_collection.name, "localField": "seeker_user_id", "foreignField": "_id", "as": "user_info"}},
            {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}}
        ]
        
        # ៣. ប្រតិបត្តិការ Query 
        cursor = job_applications_collection.aggregate(pipeline)
        app_list = await cursor.to_list(length=1)
        
        if not app_list:
            raise HTTPException(status_code=404, detail="Application not found or you don't have access to it.")
            
        # ៤. Return ទិន្នន័យចេញដោយប្រើ Format Helper ដែលមានស្រាប់
        return self._format_applicant_response(app_list[0])
    
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
    
    async def get_applicant_status_summary(self, employer_user_id: str, job_id: str) -> dict:
        """ទាញយកចំនួនបេក្ខជនសរុប ដោយបែងចែកតាម Status (ប្រើ $group Aggregation)"""
        
        employer_profile = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)})
        if not employer_profile:
            raise HTTPException(status_code=403, detail="Employer profile not found.")
            
        company_id = employer_profile["_id"]
        
        # ១. រៀបចំលក្ខខណ្ឌស្វែងរក (បើ 'all' យកការងារក្រុមហ៊ុនទាំងអស់, បើមាន id យកតែការងារនោះ)
        query = {"company_id": company_id}
        if job_id.lower() != "all":
            if not ObjectId.is_valid(job_id):
                raise HTTPException(status_code=400, detail="Invalid Job ID format.")
            query["job_id"] = ObjectId(job_id)

        # ២. បង្កើត Pipeline ដើម្បី Group តាម status និងរាប់ចំនួន (Count)
        pipeline = [
            {"$match": query},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        
        cursor = job_applications_collection.aggregate(pipeline)
        
        # ៣. រៀបចំទិន្នន័យ Default
        summary = {
            "all": 0, "pending": 0, "shortlisted": 0, 
            "interview": 0, "hired": 0, "rejected": 0
        }
        
        total_all = 0
        
        # ៤. បញ្ចូលតួលេខពិតប្រាកដដែលបានមកពី DB
        async for doc in cursor:
            status_name = doc.get("_id")
            count_val = doc.get("count", 0)
            
            if status_name in summary:
                summary[status_name] = count_val
            total_all += count_val
            
        # ៥. កំណត់ចំនួនសរុប (All)
        summary["all"] = total_all
        
        return summary

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

        # ==========================================
        # បាញ់ Notification ទៅកាន់ Seeker
        # ==========================================
        seeker_id = str(updated_app.get("seeker_user_id"))
        status_formatted = new_status.capitalize()
        
        await notification_service.create_notification(
            user_id=seeker_id,
            title="Application Updated",
            message=f"Your job application status has been updated to {status_formatted}.",
            notif_type="status_update",
            related_id=str(updated_app["_id"])
        )
        # ==========================================

        return {"application_id": str(updated_app["_id"]), "new_status": new_status} 

    # 🟢 អនុគមន៍ថ្មីសម្រាប់ធ្វើការ Update ទិន្នន័យច្រើនព្រមគ្នាក្នុង Database
    async def bulk_update_applicant_status(
        self, 
        employer_user_id: str, 
        application_ids: list, 
        new_status: str, 
        interview_schedule: dict = None, 
        feedback: str = None
    ) -> dict:
        
        if not application_ids:
            raise HTTPException(status_code=400, detail="No application IDs provided.")

        valid_statuses = ["pending", "reviewed", "shortlisted", "interview", "hired", "rejected"] 
        if new_status not in valid_statuses:
             raise HTTPException(status_code=400, detail="Status is not valid.") 

        company = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)}) 
        if not company:
             raise HTTPException(status_code=403, detail="Permission Denied") 
             
        now = datetime.now(timezone.utc)
        
        # ១. បម្លែង String IDs ទាំងអស់ទៅជា ObjectId
        try:
            object_ids = [ObjectId(app_id) for app_id in application_ids]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Application ID format in the list.")
            
        # ២. រៀបចំទិន្នន័យសម្រាប់ Update
        update_data = {
            "status": new_status, 
            "updated_at": now
        }
        
        if new_status == "interview" and interview_schedule:
             update_data["interview_schedule"] = interview_schedule
        if feedback:
             update_data["feedback"] = feedback

        # ៣. ប្រើប្រាស់ update_many ជាមួយនឹងលក្ខខណ្ឌ $in 
        result = await job_applications_collection.update_many(
            {
                "_id": {"$in": object_ids}, 
                "company_id": company["_id"] # ការពារសុវត្ថិភាព
            },
            {
                "$set": update_data,
                "$push": {"status_history": {"status": new_status, "date": now}} 
            }
        )
        
        # ==========================================
        # បាញ់ Notification ទៅគ្រប់ Seeker ដែលពាក់ព័ន្ធ
        # ==========================================
        if result.modified_count > 0:
            # ទាញយកឯកសារដែលត្រូវគ្នា ដើម្បីយក seeker_user_id
            updated_apps = await job_applications_collection.find({"_id": {"$in": object_ids}}).to_list(length=None)
            status_formatted = new_status.capitalize()
            
            for app in updated_apps:
                seeker_id = str(app.get("seeker_user_id"))
                await notification_service.create_notification(
                    user_id=seeker_id,
                    title="Application Updated",
                    message=f"Your job application status has been updated to {status_formatted}.",
                    notif_type="status_update",
                    related_id=str(app["_id"])
                )

        # ត្រឡប់ចំនួនដែលរកឃើញ និងចំនួនដែលបាន Update ពិតប្រាកដ
        return {
            "matched_count": result.matched_count, 
            "modified_count": result.modified_count,
            "new_status": new_status
        }

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