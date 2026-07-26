from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime, timezone

from src.core.mongo import job_posts_collection, company_profiles_collection

from src.domains.employer.job_post.models.job_post_model import JobPostModel
from src.domains.employer.job_post.schemas.job_post_schema import JobPostCreate, JobPostUpdate

class JobPostService:
    
    def _format_response(self, job: dict) -> dict:
        """បំប្លែងទិន្នន័យពី MongoDB ទៅជាទម្រង់ Response Schema ឱ្យបានស្អាត"""
        if not job: return None
        return {
            "id": str(job["_id"]),
            "company_id": str(job["company_id"]),
            "title": job.get("title", ""),
            "description": job.get("description", []),
            "requirements": job.get("requirements", []),
            "benefits": job.get("benefits", []),
            "min_salary": job.get("min_salary", 0),
            "max_salary": job.get("max_salary", 0),
            "salary_period": job.get("salary_period", ""),
            "is_negotiable": job.get("is_negotiable", True),
            "headcount": job.get("headcount", 1),
            "experience": job.get("experience", ""),
            "working_days": job.get("working_days", ""),
            "working_hours": job.get("working_hours", ""),
            "specific_schedule": job.get("specific_schedule"),
            "category_id": str(job.get("category_id", "")),
            "job_level_id": str(job.get("job_level_id", "")),
            "work_type_id": str(job.get("work_type_id", "")),
            "employment_type_id": str(job.get("employment_type_id", "")),
            "education_level_id": str(job.get("education_level_id", "")),
            
            # បំប្លែង Array នៃ ObjectId ទៅជា Array នៃ String វិញ
            "required_skills": [str(skill) for skill in job.get("required_skills", [])],
            "custom_skills": job.get("custom_skills", []),
            
            "province_id": str(job.get("province_id", "")),
            "district_id": str(job.get("district_id", "")) if job.get("district_id") else None,
            "closing_date": job.get("closing_date"),
            "status": job.get("status", "active"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at")
        }
        
    def _validate_foreign_keys(self, payload) -> None:
        """ឆែកមើលថាតើ ID ទាំងអស់ពិតជាទម្រង់ ObjectId របស់ MongoDB ត្រឹមត្រូវឬអត់"""
        
        # ប្រមូលផ្តុំ IDs ទាំងអស់ (យើងប្រើ getattr ដើម្បីឱ្យវាគាំទ្រទាំង Create និង Update)
        ids_to_check = {
            "category_id": getattr(payload, "category_id", None),
            "job_level_id": getattr(payload, "job_level_id", None),
            "work_type_id": getattr(payload, "work_type_id", None),
            "employment_type_id": getattr(payload, "employment_type_id", None),
            "education_level_id": getattr(payload, "education_level_id", None),
            "province_id": getattr(payload, "province_id", None),
            "district_id": getattr(payload, "district_id", None)
        }

        # ១. ឆែកមើល ID តែម្តងៗ (Single IDs)
        for field_name, id_val in ids_to_check.items():
            # បើមានបញ្ចូលតម្លៃ ហើយតម្លៃនោះមិនមែនជា ObjectId
            if id_val and not ObjectId.is_valid(id_val):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid data: '{field_name}' is not a valid ID format."
                )

        # ២. ឆែកមើល Array នៃ IDs (Skills)
        required_skills = getattr(payload, "required_skills", [])
        if required_skills:
            for skill_id in required_skills:
                if not ObjectId.is_valid(skill_id):
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid data: skill '{skill_id}' is not a valid ID format."
                    )

    
    async def create_job_post(self, user_id: str, payload: JobPostCreate) -> dict:
        """មុខងារសម្រាប់បង្កើតការងារថ្មី"""
        user_oid = ObjectId(user_id)

        # ១. ផ្ទៀងផ្ទាត់ថាតើ Employer នេះមាន Company Profile ហើយឬនៅ?
        # (មានតែ Employer ដែលមានក្រុមហ៊ុនទេ ទើបអាចប្រកាសការងារបាន)
        company = await company_profiles_collection.find_one({"user_id": user_oid})
        if not company:
            raise HTTPException(
                status_code=403, 
                detail="You must have a company profile to create a job post."
            )

        # ២. ទាញយក company_id ពីប្រវត្តិរូបក្រុមហ៊ុនរបស់គាត់
        company_id = company["_id"]
        
        self._validate_foreign_keys(payload)
            
        # ៣. បញ្ចូលទិន្នន័យទៅក្នុង Model ដើម្បីបំប្លែង String ID ទៅជា ObjectId 
        # និងបង្កើត Timestamp (created_at, updated_at)
        new_job_model = JobPostModel(
            company_id=company_id,
            **payload.model_dump()
        )
        
        # ៤. ទាញយកទម្រង់ Dictionary ដែលរួចរាល់សម្រាប់ការ Save
        new_job_dict = new_job_model.to_create_dict()

        # ៥. Save ចូល Database ក្នុងតារាង job_posts
        await job_posts_collection.insert_one(new_job_dict)

        # ៦. បោះទិន្នន័យដែលទើបតែ Save រួចត្រឡប់ទៅឱ្យ Router វិញ
        return self._format_response(new_job_dict)
    
    async def get_my_job_posts(
        self, 
        user_id: str, 
        search: str = None, 
        status: str = None, 
        page: int = 1, 
        limit: int = 10
    ) -> list:
        """ទាញយកបញ្ជីការងារទាំងអស់ដែលក្រុមហ៊ុននេះបាន Post ព្រមទាំងអាច Search និង Filter បាន"""
        user_oid = ObjectId(user_id)

        # ១. រកមើល Company របស់ Employer
        company = await company_profiles_collection.find_one({"user_id": user_oid})
        if not company:
            return []

        company_id = company["_id"]

        # ២. រៀបចំ Query សម្រាប់ Search និង Filter
        query = {"company_id": company_id}
        
        # ក. ស្វែងរកតាមចំណងជើងការងារ (Title) - មិនប្រកាន់អក្សរតូចធំ (Case-insensitive)
        if search:
            query["title"] = {"$regex": search, "$options": "i"}
            
        # ខ. ត្រងតាមស្ថានភាព (Status) ឧ. active, inactive, closed, draft
        if status and status.lower() != "all":
            query["status"] = status.lower()

        # ៣. គណនាការកាត់ទំព័រ (Pagination)
        skip = (page - 1) * limit

        # ៤. ទាញយកការងារទាំងអស់តាម Query ខាងលើ 
        # .sort("created_at", -1) រៀបតាមថ្ងៃ Post ថ្មីបំផុតឱ្យនៅខាងលើគេ
        cursor = job_posts_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        # ៥. បំប្លែងទិន្នន័យ (Format) ហើយដាក់ចូលក្នុង Array
        jobs = []
        async for job in cursor:
            jobs.append(self._format_response(job))

        return jobs
    
    async def get_job_post_by_id(self, user_id: str, job_id: str) -> dict:
        """ទាញយកព័ត៌មានលម្អិតនៃការងារណាមួយ (Get Job by ID)"""
        
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="ID is not valid.")

        # ១. រកមើល Company របស់ Employer សិន
        company = await company_profiles_collection.find_one({"user_id": ObjectId(user_id)})
        if not company:
            raise HTTPException(status_code=403, detail="You must have a company profile.")

        # ២. ទាញយកការងារដោយបញ្ជាក់ ID ព្រមទាំងឆែកថាជារបស់ក្រុមហ៊ុននេះពិតមែន (សុវត្ថិភាព)
        job = await job_posts_collection.find_one({
            "_id": ObjectId(job_id),
            "company_id": company["_id"]
        })

        if not job:
            raise HTTPException(
                status_code=404, 
                detail="Job post not found or you don't have permission to view it."
            )

        return self._format_response(job)
    
    async def update_job_post(self, user_id: str, job_id: str, payload: JobPostUpdate) -> dict:
        """មុខងារសម្រាប់កែប្រែការងារចាស់"""
        
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="ID is not valid.")

        # ១. រកមើល Company របស់ Employer សិន
        company = await company_profiles_collection.find_one({"user_id": ObjectId(user_id)})
        if not company:
            raise HTTPException(status_code=403, detail="You must have a company profile to update a job post.")

        # ២. 🛡️ សុវត្ថិភាពទិន្នន័យ៖ ស្វែងរកការងារនោះ ព្រមទាំងឆែកថាវាជារបស់ក្រុមហ៊ុននេះពិតមែនអត់?
        existing_job = await job_posts_collection.find_one({
            "_id": ObjectId(job_id),
            "company_id": company["_id"]
        })

        if not existing_job:
            raise HTTPException(
                status_code=404, 
                detail="Job post not found or you don't have permission to update it."
            )

        # ៣. ឆែក Validation លើ Foreign Keys ដោយប្រើ Helper Function ដែលយើងទើបបង្កើត
        self._validate_foreign_keys(payload)

        # ៤. រៀបចំទិន្នន័យសម្រាប់ Update (ទាញយកតែ Field ដែល Employer បានបញ្ជូនមក)
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update.")

        # ៥. បំប្លែង String ID ទៅជា ObjectId សម្រាប់ Field ណាដែលមានការកែប្រែ
        id_fields = [
            "category_id", "job_level_id", "work_type_id", 
            "employment_type_id", "education_level_id", 
            "province_id", "district_id"
        ]
        
        for field in id_fields:
            if field in update_data and update_data[field]:
                update_data[field] = ObjectId(update_data[field])

        if "required_skills" in update_data:
            update_data["required_skills"] = [ObjectId(skill) for skill in update_data["required_skills"]]

        if "closing_date" in update_data:
            update_data["closing_date"] = update_data["closing_date"].replace(tzinfo=timezone.utc)

        update_data["updated_at"] = datetime.now(timezone.utc)

        # ៦. Update ចូល Database
        updated_job = await job_posts_collection.find_one_and_update(
            {"_id": ObjectId(job_id)},
            {"$set": update_data},
            return_document=True
        )

        return self._format_response(updated_job)
    
    async def delete_job_post(self, user_id: str, job_id: str) -> dict:
        """មុខងារសម្រាប់លុបការងារជាអចិន្ត្រៃយ៍ (Hard Delete)"""
        
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="ID is not valid.")

        # ១. រកមើល Company របស់ Employer
        company = await company_profiles_collection.find_one({"user_id": ObjectId(user_id)})
        if not company:
            raise HTTPException(status_code=403, detail="You must have a company profile to delete a job post.")

        # ២. 🛡️ សុវត្ថិភាពទិន្នន័យ៖ លុបតែការងារណាដែលជារបស់ក្រុមហ៊ុននេះប៉ុណ្ណោះ
        result = await job_posts_collection.delete_one({
            "_id": ObjectId(job_id),
            "company_id": company["_id"] # ការពារមិនឱ្យលុបការងារអ្នកដទៃ
        })

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404, 
                detail="Job post not found or you don't have permission to delete it."
            )

        return {"success": True}
    
    async def change_job_status(self, user_id: str, job_id: str, new_status: str) -> dict:
        """មុខងារសម្រាប់ឱ្យ Employer ប្តូរស្ថានភាពការងារ (ឧ. active, closed, draft) យ៉ាងរហ័ស"""
        
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="ID is not valid.")
            
        # ១. អនុញ្ញាតតែ Status ទាំងនេះប៉ុណ្ណោះ
        allowed_statuses = ["active", "inactive", "closed", "draft"]
        if new_status not in allowed_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Allowed values are: {', '.join(allowed_statuses)}"
            )

        # ២. ឆែករក Company របស់ Employer
        company = await company_profiles_collection.find_one({"user_id": ObjectId(user_id)})
        if not company:
            raise HTTPException(status_code=403, detail="You must have a company profile.")

        # ៣. Update Status ក្នុង Database ដោយប្រាកដថាការងារនោះជារបស់ក្រុមហ៊ុនគាត់មែន
        updated_job = await job_posts_collection.find_one_and_update(
            {
                "_id": ObjectId(job_id),
                "company_id": company["_id"]
            },
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            return_document=True
        )

        if not updated_job:
            raise HTTPException(status_code=404, detail="Job post not found or permission denied.")

        return self._format_response(updated_job)