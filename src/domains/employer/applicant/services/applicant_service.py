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
        """ទាញយកបញ្ជីអ្នកដាក់ពាក្យ ដោយចាត់ថ្នាក់តាម Job នីមួយៗ (ឬគ្រប់ Job ទាំងអស់ បើ job_id == "all")"""

        # ១. ឆែកមើល Company របស់ Employer
        company = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)})
        if not company:
            raise HTTPException(status_code=403, detail="company profile not found for this employer.")

        # ២. រៀបចំ Query តាម Job — Flutter ផ្ញើ job_id="all" ជា Default (Candidates tab មិនបានជ្រើសរើស
        # Job ណាមួយជាក់លាក់ទេ) ដែលមិនមែនជា ObjectId ត្រឹមត្រូវ ដូច្នេះត្រូវដោះស្រាយវាដាច់ដោយឡែក —
        # មិនអញ្ជើញ ObjectId("all") ដែលនឹង Throw InvalidId Error ទេ។
        if job_id.lower() == "all":
            job_ids = [
                doc["_id"]
                async for doc in job_posts_collection.find({"company_id": company["_id"]}, {"_id": 1})
            ]
            query: dict = {"job_id": {"$in": job_ids}}
        else:
            # ឆែកមើល Job ថាជារបស់ក្រុមហ៊ុនគាត់ពិតមែនឬអត់ (សុវត្ថិភាពទិន្នន័យ)
            job = await job_posts_collection.find_one({
                "_id": ObjectId(job_id),
                "company_id": company["_id"]
            })
            if not job:
                raise HTTPException(status_code=404, detail="Job not found or it does not belong to you.")
            query = {"job_id": ObjectId(job_id)}

        if status_filter and status_filter.lower() != "all":
            query["status"] = status_filter.lower()

        # ៣. Join ទិន្នន័យ Application ជាមួយ Seeker Profile និង Job (សម្រាប់ job_title, មានប្រយោជន៍
        # ជាពិសេសពេលមើល "All Jobs" ព្រោះបេក្ខជននីមួយៗអាចដាក់ពាក្យលើ Job ខុសៗគ្នា)
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
            {"$unwind": {"path": "$seeker_info", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": job_posts_collection.name,
                    "localField": "job_id",
                    "foreignField": "_id",
                    "as": "job_info"
                }
            },
            {"$unwind": {"path": "$job_info", "preserveNullAndEmptyArrays": True}},
        ]

        cursor = job_applications_collection.aggregate(pipeline)

        applicants = []
        async for app in cursor:
            seeker = app.get("seeker_info", {}) or {}
            job_info = app.get("job_info", {}) or {}
            applicants.append({
                "application_id": str(app["_id"]),
                "seeker_user_id": str(app["seeker_user_id"]),
                "first_name": seeker.get("first_name", "Unknown"),
                "last_name": seeker.get("last_name", ""),
                "profile_image_url": seeker.get("profile_image_url"),
                "current_position": seeker.get("current_position", ""),
                "resume_url": app.get("resume_url"),
                "cover_letter": app.get("cover_letter"),
                "status": app.get("status"),
                "applied_at": app.get("applied_at"),
                "job_title": job_info.get("title", "Unknown"),
            })

        return applicants

    async def get_job_dropdown(self, employer_user_id: str) -> list:
        """ទាញយកបញ្ជី Job ទាំងអស់របស់ក្រុមហ៊ុននេះ សម្រាប់ Dropdown ជ្រើសរើសនៅលើអេក្រង់ Candidates"""

        company = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)})
        if not company:
            raise HTTPException(status_code=403, detail="company profile not found for this employer.")

        cursor = job_posts_collection.find(
            {"company_id": company["_id"]},
            sort=[("created_at", -1)],
        )

        jobs = []
        async for job in cursor:
            jobs.append({
                "job_id": str(job["_id"]),
                "display_name": job.get("title", "Untitled Job"),
                "status": job.get("status", "active"),
            })

        return jobs

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

    async def get_all_seekers(
        self,
        employer_user_id: str,
        search: str | None = None,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        """ទាញយកបញ្ជីគណនី Seeker ទាំងអស់ក្នុងប្រព័ន្ធ (Active) សម្រាប់ Employer ជ្រើសរើសចាប់ផ្ដើម Chat ថ្មី
        មិនកំណត់ត្រឹមតែ Seeker ដែលធ្លាប់ដាក់ពាក្យមកខ្លួនឯងទេ គឺបង្ហាញ Seeker គ្រប់គណនី។
        """

        company = await company_profiles_collection.find_one({"user_id": ObjectId(employer_user_id)})
        if not company:
            raise HTTPException(status_code=403, detail="company profile not found for this employer.")

        # ១. រៀបចំ Query មូលដ្ឋាន៖ គណនីតួនាទី seeker និងកំពុង Active
        match_stage: dict = {"role": "seeker", "is_active": True}
        if search:
            # ស្វែងរកតាមឈ្មោះ (មិនប្រកាន់អក្សរតូចធំ)
            match_stage["$or"] = [
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}}
            ]

        skip = (page - 1) * limit

        pipeline = [
            {"$match": match_stage},
            {"$sort": {"created_at": -1}},
            {
                "$lookup": {
                    "from": seeker_profiles_collection.name,
                    "localField": "_id",
                    "foreignField": "user_id",
                    "as": "seeker_info"
                }
            },
            {"$unwind": {"path": "$seeker_info", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": job_applications_collection.name,
                    "localField": "_id",
                    "foreignField": "seeker_user_id",
                    "as": "applications_to_any_company"
                }
            },
            {
                "$facet": {
                    "data": [{"$skip": skip}, {"$limit": limit}],
                    "total_count": [{"$count": "count"}]
                }
            }
        ]

        cursor = users_collection.aggregate(pipeline)
        raw_result = await cursor.to_list(length=1)
        facet = raw_result[0] if raw_result else {"data": [], "total_count": []}

        total = facet["total_count"][0]["count"] if facet["total_count"] else 0

        my_company_id = company["_id"]
        items = []
        for u in facet["data"]:
            seeker = u.get("seeker_info", {}) or {}
            applications = u.get("applications_to_any_company", []) or []
            has_applied_to_me = any(
                app.get("company_id") == my_company_id for app in applications
            )
            items.append({
                "seeker_user_id": str(u["_id"]),
                "first_name": u.get("first_name", "Unknown"),
                "last_name": u.get("last_name", ""),
                "profile_image_url": seeker.get("image_url") or u.get("avatar_url"),
                "current_position": seeker.get("current_position", ""),
                "has_applied_to_you": has_applied_to_me
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": skip + len(items) < total
        }