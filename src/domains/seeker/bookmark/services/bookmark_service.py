from bson import ObjectId
from fastapi import HTTPException
from datetime import datetime, timezone
from src.core.mongo import saved_jobs_collection, job_posts_collection
from src.domains.seeker.job_feed.services.job_feed_service import JobFeedService

job_feed_service = JobFeedService()

class BookmarkService:
    
    async def toggle_bookmark(self, user_id: str, job_id: str) -> dict:
        """Toggle save and unsave a job."""
        user_oid = ObjectId(user_id)
        job_oid = ObjectId(job_id)

        # Check whether the job exists and is active.
        job = await job_posts_collection.find_one({"_id": job_oid, "status": "active"})
        if not job:
            raise HTTPException(status_code=404, detail="Job post not found or inactive.")

        # Check whether the seeker has already saved this job.
        existing_bookmark = await saved_jobs_collection.find_one({
            "user_id": user_oid,
            "job_id": job_oid
        })

        if existing_bookmark:
            # If the job is already saved, remove it from the saved list.
            await saved_jobs_collection.delete_one({"_id": existing_bookmark["_id"]})
            return {"is_saved": False, "message": "Job removed from your saved list."}
        else:
            # If the job is not saved yet, add it to the saved list.
            await saved_jobs_collection.insert_one({
                "user_id": user_oid,
                "job_id": job_oid,
                "created_at": datetime.now(timezone.utc)
            })
            return {"is_saved": True, "message": "Job saved successfully."} 

    async def get_saved_jobs(self, user_id: str, page: int = 1, limit: int = 10) -> list:
        """Retrieve all jobs saved by a seeker."""
        skip = (page - 1) * limit
        user_oid = ObjectId(user_id)

        # Retrieve all saved job IDs for this seeker, ordered by latest save date.
        cursor = saved_jobs_collection.find({"user_id": user_oid}).sort("created_at", -1).skip(skip).limit(limit)
        saved_docs = await cursor.to_list(length=limit)
        
        if not saved_docs:
            return []

        # Collect the saved job IDs into an array.
        job_ids = [doc["job_id"] for doc in saved_docs]

        # Reuse the JobFeedService pipeline to fetch complete job data.
        match_condition = {"_id": {"$in": job_ids}}
        sort_stage = {"$sort": {"created_at": -1}}
        
        # Reuse the pipeline to get the standard join response structure.
        pipeline = job_feed_service._build_pipeline(
            user_oid=user_oid,
            skip=0, # Already skipped above.
            limit=limit,
            match_condition=match_condition,
            sort_stage=sort_stage,
            seeker_profile=None, # Optionally include match percentage in the saved list.
            weights={"category": 30, "province": 10, "district": 10, "skill": 50}
        )

        job_cursor = job_posts_collection.aggregate(pipeline)
        
        saved_jobs = []
        async for job in job_cursor:
            # The formatter should produce an "is_saved": True response automatically.
            saved_jobs.append(job_feed_service._format_feed_response(job))

        return saved_jobs