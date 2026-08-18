from bson import ObjectId
from src.core.mongo import (
    job_posts_collection, 
    job_applications_collection, 
    company_profiles_collection,
    seeker_profiles_collection,
    users_collection
)
from src.domains.employer.employer_dashboard.models.employer_dashboard_model import (
    EmployerDashboardResponse, 
    OverviewStatsModel, 
    PipelineStatsModel, 
    RecentApplicantModel
)
from src.domains.employer.employer_dashboard.utils.date_utils import get_dashboard_date_ranges

class EmployerDashboardService:

    # អនុគមន៍ជំនួយសម្រាប់គណនា Trend (ឧទាហរណ៍ +3, -1)
    def _calc_trend(self, current: int, previous: int) -> str:
        diff = current - previous
        if diff > 0:
            return f"↗ +{diff}"
        elif diff < 0:
            return f"↘ {diff}"
        return "0"

    async def get_dashboard_data(self, user_id: str, filter_str: str) -> EmployerDashboardResponse:
        user_oid = ObjectId(user_id)
        
        # ១. រកមើល Company
        company = await company_profiles_collection.find_one({"user_id": user_oid})
        if not company:
            raise Exception("Company profile not found")
            
        company_id = company["_id"]

        # ២. ទាញយកថ្ងៃខែសម្រាប់ Filter
        (curr_start, curr_end), (prev_start, prev_end) = get_dashboard_date_ranges(filter_str)

        # ៣. ទាញយក Job IDs ទាំងអស់របស់ក្រុមហ៊ុន ដើម្បីយកទៅ Query Applications ងាយស្រួល
        company_jobs_cursor = job_posts_collection.find(
            {"company_id": company_id}, 
            {"_id": 1, "title": 1, "status": 1}
        )
        company_jobs = await company_jobs_cursor.to_list(None)
        
        job_ids = [job["_id"] for job in company_jobs]
        active_job_ids = [job["_id"] for job in company_jobs if job.get("status") == "active"]
        job_title_map = {job["_id"]: job.get("title", "Unknown Job") for job in company_jobs}

        # ---------------------------------------------------------
        # ៤. Query Data សម្រាប់ Overview Stats (កាតទាំង ៤)
        # ---------------------------------------------------------
        # ក. Jobs Posted
        curr_jobs = await job_posts_collection.count_documents({
            "company_id": company_id,
            "created_at": {"$gte": curr_start, "$lte": curr_end}
        })
        prev_jobs = await job_posts_collection.count_documents({
            "company_id": company_id,
            "created_at": {"$gte": prev_start, "$lte": prev_end}
        })

        # បើគ្មានការងារសោះ យើងមិនបាច់ Query Application នាំខាតពេលទេ
        curr_apps = prev_apps = curr_interviews = prev_interviews = curr_hired = prev_hired = 0
        
        if job_ids:
            # ខ. Total Applications
            curr_apps = await job_applications_collection.count_documents({
                "job_id": {"$in": job_ids},
                "applied_at": {"$gte": curr_start, "$lte": curr_end}
            })
            prev_apps = await job_applications_collection.count_documents({
                "job_id": {"$in": job_ids},
                "applied_at": {"$gte": prev_start, "$lte": prev_end}
            })

            # គ. Interviews (ប្រើ updated_at ព្រោះ Status អាចប្រែប្រួលតាមក្រោយ)
            curr_interviews = await job_applications_collection.count_documents({
                "job_id": {"$in": job_ids},
                "status": "interview",
                "updated_at": {"$gte": curr_start, "$lte": curr_end}
            })
            prev_interviews = await job_applications_collection.count_documents({
                "job_id": {"$in": job_ids},
                "status": "interview",
                "updated_at": {"$gte": prev_start, "$lte": prev_end}
            })

            # ឃ. Hired / Offer
            curr_hired = await job_applications_collection.count_documents({
                "job_id": {"$in": job_ids},
                "status": {"$in": ["hired", "offer"]},
                "updated_at": {"$gte": curr_start, "$lte": curr_end}
            })
            prev_hired = await job_applications_collection.count_documents({
                "job_id": {"$in": job_ids},
                "status": {"$in": ["hired", "offer"]},
                "updated_at": {"$gte": prev_start, "$lte": prev_end}
            })

        overview = OverviewStatsModel(
            jobs_posted=curr_jobs,
            jobs_posted_trend=self._calc_trend(curr_jobs, prev_jobs),
            
            total_applications=curr_apps,
            applications_trend=self._calc_trend(curr_apps, prev_apps),
            
            interviews=curr_interviews,
            interviews_trend=self._calc_trend(curr_interviews, prev_interviews),
            
            hired=curr_hired,
            hired_trend=self._calc_trend(curr_hired, prev_hired)
        )

        # ---------------------------------------------------------
        # ៥. Query Data សម្រាប់ Pipeline (Screening, Review...)
        # ---------------------------------------------------------
        # យើង Group តាម status តែសម្រាប់ការងារដែល Active ប៉ុណ្ណោះ
        pipeline_data = {"pending": 0, "screening": 0, "review": 0, "interview": 0, "offer": 0, "hired": 0}
        total_active_candidates = 0
        
        if active_job_ids:
            pipeline_cursor = job_applications_collection.aggregate([
                {"$match": {"job_id": {"$in": active_job_ids}}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ])
            
            async for doc in pipeline_cursor:
                status = str(doc["_id"]).lower() if doc["_id"] else "pending"
                count = doc.get("count", 0)
                pipeline_data[status] = pipeline_data.get(status, 0) + count
                
                # បូកបញ្ចូលបេក្ខជនទាំងអស់ដែលមិនទាន់ធ្លាក់ (Rejected/Withdrawn)
                if status not in ["rejected", "withdrawn"]:
                    total_active_candidates += count

        # ផ្គូផ្គង Status របស់ Database ទៅកាន់ UI របស់ Pipeline
        pipeline = PipelineStatsModel(
            active_candidates=total_active_candidates,
            screening=pipeline_data.get("pending", 0) + pipeline_data.get("screening", 0) + pipeline_data.get("applied", 0),
            review=pipeline_data.get("review", 0) + pipeline_data.get("shortlisted", 0),
            interview=pipeline_data.get("interview", 0),
            offer=pipeline_data.get("offer", 0) + pipeline_data.get("hired", 0)
        )

        # ---------------------------------------------------------
        # ៦. Query Data សម្រាប់ Recent Applicants (៥ នាក់ចុងក្រោយ)
        # ---------------------------------------------------------
        recent_applicants = []
        if job_ids:
            # ស្វែងរក ៥ នាក់ចុងក្រោយ
            recent_cursor = job_applications_collection.find(
                {"job_id": {"$in": job_ids}}
            ).sort("applied_at", -1).limit(5)
            
            async for app in recent_cursor:
                seeker_id = app.get("seeker_user_id")
                
                profile = None
                user_account = None 
                
                if seeker_id:
                    if isinstance(seeker_id, str) and ObjectId.is_valid(seeker_id):
                        seeker_oid = ObjectId(seeker_id)
                    elif isinstance(seeker_id, ObjectId):
                        seeker_oid = seeker_id
                    else:
                        seeker_oid = None
                    
                    if seeker_oid:
                        user_account = await users_collection.find_one({"_id": seeker_oid})
                        profile = await seeker_profiles_collection.find_one({"user_id": seeker_oid})
                
                # 🟢 រៀបចំឈ្មោះ (យកពី user_account)
                first_name = user_account.get("first_name", "") if user_account else ""
                last_name = user_account.get("last_name", "") if user_account else ""
                full_name = f"{first_name} {last_name}".strip() or "Unknown Candidate"
                
                # 🟢 រៀបចំរូបភាព (យកពី profile)
                avatar_url = profile.get("profile_image_url", "") if profile else ""
                
                # បញ្ចូលទៅក្នុងបញ្ជី
                recent_applicants.append(RecentApplicantModel(
                    applicant_id=str(app["_id"]),
                    seeker_id=str(seeker_id),
                    name=full_name,
                    avatar_url=avatar_url,
                    job_title=job_title_map.get(app.get("job_id"), "Unknown Job"),
                    status=str(app.get("status", "pending")).capitalize(),
                    applied_at=app.get("applied_at"),
                    rating=float(app.get("rating", 0.0))
                ))

        # ---------------------------------------------------------
        # ៧. បោះលទ្ធផលត្រលប់ទៅវិញ
        # ---------------------------------------------------------
        return EmployerDashboardResponse(
            overview=overview,
            pipeline=pipeline,
            recent_applicants=recent_applicants
        )

# Create Singleton Instance
employer_dashboard_service = EmployerDashboardService()