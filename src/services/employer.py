from datetime import datetime
from bson import ObjectId, errors
from src.config.mongo import collections

def insert_job(job_data: dict):
    """Create a new job posting"""
    job_col = collections("jobs")
    
    # Add timestamps
    job_data["created_at"] = datetime.now()
    job_data["updated_at"] = datetime.now()
    job_data["is_active"] = True
    
    result = job_col.insert_one(job_data)
    
    if result.inserted_id:
        return {
            "success": True,
            "message": "Job posted successfully",
            "job_id": str(result.inserted_id)
        }
    return {"success": False, "message": "Failed to post job"}

def get_all_jobs():
    """Get all active jobs"""
    job_col = collections("jobs")
    jobs = list(job_col.find({"is_active": True}))
    
    for job in jobs:
        job["_id"] = str(job["_id"])
        job.pop("password", None)
    
    return jobs

def get_job_by_id(job_id: str):
    """Get a single job by ID"""
    try:
        job_col = collections("jobs")
        job = job_col.find_one({"_id": ObjectId(job_id), "is_active": True})
        
        if job:
            job["_id"] = str(job["_id"])
            return job
        return None
    except errors.InvalidId:
        return None

def update_job(job_id: str, update_data: dict):
    """Update a job posting"""
    try:
        job_col = collections("jobs")
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.now()
        
        result = job_col.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return {"success": False, "message": "Job not found"}
        
        if result.modified_count > 0:
            return {"success": True, "message": "Job updated successfully"}
        return {"success": True, "message": "No changes made"}
        
    except errors.InvalidId:
        return {"success": False, "message": "Invalid job ID"}

def delete_job(job_id: str):
    """Soft delete a job (set is_active to False)"""
    try:
        job_col = collections("jobs")
        
        result = job_col.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"is_active": False, "updated_at": datetime.now()}}
        )
        
        if result.matched_count == 0:
            return {"success": False, "message": "Job not found"}
        
        return {"success": True, "message": "Job deleted successfully"}
        
    except errors.InvalidId:
        return {"success": False, "message": "Invalid job ID"}

def search_jobs(location: str = None, job_type: str = None, keyword: str = None):
    """Search jobs by filters"""
    job_col = collections("jobs")
    query = {"is_active": True}
    
    if location:
        query["location"] = location
    if job_type:
        query["job_type"] = job_type
    if keyword:
        query["$or"] = [
            {"job_title": {"$regex": keyword, "$options": "i"}},
            {"job_description": {"$regex": keyword, "$options": "i"}}
        ]
    
    jobs = list(job_col.find(query))
    
    for job in jobs:
        job["_id"] = str(job["_id"])
    
    return jobs
