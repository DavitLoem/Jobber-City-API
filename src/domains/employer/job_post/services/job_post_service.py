from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime, timezone

from src.core.mongo import job_posts_collection, company_profiles_collection

from src.domains.employer.job_post.models.job_post_model import JobPostModel
from src.domains.employer.job_post.schemas.job_post_schema import JobPostCreate

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
            
            "province_id": str(job.get("province_id", "")),
            "district_id": str(job.get("district_id", "")) if job.get("district_id") else None,
            "closing_date": job.get("closing_date"),
            "status": job.get("status", "active"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at")
        }

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