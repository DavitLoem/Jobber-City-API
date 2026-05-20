from fastapi import APIRouter, HTTPException, Body, Query, UploadFile, File, Form
from typing import Optional, List
from src.model.employer import PostJobRequest, Location, JobType, WorkplaceType
from src.services.employer import insert_job, get_all_jobs, get_job_by_id, update_job, delete_job, search_jobs
from src.config.cloudinary import upload_image, delete_image
import json

router = APIRouter(prefix="/api/employer", tags=["Employer"])


@router.post("/post-job", summary="Post a new job")
async def post_job(
    image: UploadFile = File(..., description="Company or job image"),
    job_title: str = Form(..., min_length=3, max_length=100),
    location: Location = Form(...),
    salary: str = Form(...),
    job_type: JobType = Form(...),
    workplace_type: WorkplaceType = Form(...),
    job_description: str = Form(..., min_length=10, max_length=1000),
    minimum_qualifications: str = Form(..., min_length=3, max_length=100),
    perks_and_benefits: Optional[str] = Form(None, description="JSON array or comma-separated"),
    required_skills: Optional[str] = Form(None, description="JSON array or comma-separated"),
    job_level: str = Form(...),
    job_category: str = Form(...),
    educational_level: str = Form(...),
    experience_years: str = Form(...),
    vacancy_count: int = Form(default=1, ge=1),
    company_website: Optional[str] = Form(None),
    about_company: str = Form(..., min_length=50),
    application_deadline: str = Form(...)
):
    try:
 
        image_result = upload_image(image.file)
        
        if not image_result["success"]:
            raise HTTPException(status_code=400, detail=f"Image upload failed: {image_result.get('message')}")
        
        def parse_list(value, field_name):
            if not value:
                return []
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                print(f"[DEBUG] {field_name} not JSON, trying comma-split: {value}")
                return [item.strip() for item in value.split(",") if item.strip()]
        
        perks_list = parse_list(perks_and_benefits, "perks_and_benefits")
        skills_list = parse_list(required_skills, "required_skills")
        
        print(f"[DEBUG] Parsed perks: {perks_list}, skills: {skills_list}")
        
        job_data = {
            "image": image_result["url"],
            "image_public_id": image_result["public_id"],
            "job_title": job_title,
            "location": location.value,
            "salary": salary,
            "job_type": job_type.value,
            "workplace_type": workplace_type.value,
            "job_description": job_description,
            "minimum_qualifications": minimum_qualifications,
            "perks_and_benefits": perks_list,
            "required_skills": skills_list,
            "job_level": job_level,
            "job_category": job_category,
            "educational_level": educational_level,
            "experience_years": experience_years,
            "vacancy_count": vacancy_count,
            "company_website": company_website,
            "about_company": about_company,
            "application_deadline": application_deadline
        }
        
        result = insert_job(job_data)
        
        if not result["success"]:
            delete_image(image_result["public_id"])
            raise HTTPException(status_code=400, detail=result["message"])
        
        return {
            "status": "success",
            "message": result["message"],
            "job_id": result["job_id"],
            "image_url": image_result["url"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in post_job: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/jobs", summary="Get all jobs")
async def list_jobs():
    jobs = get_all_jobs()
    return {
        "status": "success",
        "count": len(jobs),
        "data": jobs
    }

@router.get("/jobs/{job_id}", summary="Get job by ID")
async def get_job(job_id: str):
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "status": "success",
        "data": job
    }

@router.get("/jobs/search", summary="Search jobs")
async def search(
    location: str = Query(None, description="Filter by location"),
    job_type: str = Query(None, description="Filter by job type"),
    keyword: str = Query(None, description="Search keyword")
):
    jobs = search_jobs(location=location, job_type=job_type, keyword=keyword)
    return {
        "status": "success",
        "count": len(jobs),
        "data": jobs
    }

@router.put("/jobs/{job_id}", summary="Update job")
async def update_job_endpoint(
    job_id: str,
    image: Optional[UploadFile] = File(None, description="Optional new image"),
    job_title: str = Form(...),
    location: Location = Form(...),
    salary: str = Form(...),
    job_type: JobType = Form(...),
    workplace_type: WorkplaceType = Form(...),
    job_description: str = Form(...),
    minimum_qualifications: str = Form(...),
    perks_and_benefits: Optional[str] = Form(None),
    required_skills: str = Form(...),
    job_level: str = Form(...),
    job_category: str = Form(...),
    educational_level: str = Form(...),
    experience_years: str = Form(...),
    vacancy_count: int = Form(...),
    company_website: Optional[str] = Form(None),
    about_company: str = Form(...),
    application_deadline: str = Form(...)
):

    existing_job = get_job_by_id(job_id)
    if not existing_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = {
        "job_title": job_title,
        "location": location.value,
        "salary": salary,
        "job_type": job_type.value,
        "workplace_type": workplace_type.value,
        "job_description": job_description,
        "minimum_qualifications": minimum_qualifications,
        "perks_and_benefits": json.loads(perks_and_benefits) if perks_and_benefits else [],
        "required_skills": json.loads(required_skills),
        "job_level": job_level,
        "job_category": job_category,
        "educational_level": educational_level,
        "experience_years": experience_years,
        "vacancy_count": vacancy_count,
        "company_website": company_website,
        "about_company": about_company,
        "application_deadline": application_deadline
    }
    
    if image:
        image_result = upload_image(image.file)
        if not image_result["success"]:
            raise HTTPException(status_code=400, detail=f"Image upload failed: {image_result.get('message')}")
        
        update_data["image"] = image_result["url"]
        update_data["image_public_id"] = image_result["public_id"]
        
        old_public_id = existing_job.get("image_public_id")
        if old_public_id:
            delete_image(old_public_id)
    
    result = update_job(job_id, update_data)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "status": "success",
        "message": result["message"],
        "image_url": update_data.get("image")
    }

@router.delete("/jobs/{job_id}", summary="Delete job")
async def delete_job_endpoint(job_id: str):
    job = get_job_by_id(job_id)
    if job and job.get("image_public_id"):

        delete_image(job["image_public_id"])
        
    result = delete_job(job_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "status": "success",
        "message": result["message"]
    }
