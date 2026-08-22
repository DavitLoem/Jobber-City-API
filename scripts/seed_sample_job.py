"""
Creates a few sample job posts under your FIRST employer/company account,
so you can immediately test the seeker job feed + "Message Employer" chat
feature without clicking through the "Post a Job" form by hand.

Prerequisites (run once, in order):
    1. python -m scripts.seed_master_data   (categories, job levels, etc.)
    2. Log in as an employer in the app and finish company profile setup
       at least once (this script attaches jobs to your first company).

Run from the backend project root, with your venv active:

    cd Jobber-City-API
    source .venv/bin/activate
    python -m scripts.seed_sample_job

Safe to re-run — it checks by title before inserting, so it won't create
duplicates.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from src.core.mongo import (
    company_profiles_collection,
    job_posts_collection,
    categories_collection,
    job_levels_collection,
    education_levels_collection,
    employment_types_collection,
    work_types_collection,
    skills_collection,
    provinces_collection,
)

SAMPLE_JOBS = [
    {
        "title": "Backend Developer (FastAPI)",
        "description": ["Build and maintain REST APIs powering our mobile app.", "Work closely with the mobile team on new features."],
        "requirements": ["1+ years experience with Python", "Familiarity with MongoDB", "Comfortable with Git"],
        "benefits": ["Health insurance", "Flexible hours", "Annual bonus"],
        "min_salary": 500,
        "max_salary": 900,
        "job_level": "Mid Level",
        "employment_type": "Full-time",
        "work_type": "Remote",
        "skills": ["Python", "FastAPI", "MongoDB"],
    },
    {
        "title": "Flutter Mobile Developer",
        "description": ["Develop and maintain our cross-platform mobile app.", "Collaborate with backend and design teams."],
        "requirements": ["Experience with Flutter/Dart", "Understanding of REST APIs", "Basic Git knowledge"],
        "benefits": ["Health insurance", "Remote-friendly", "Learning budget"],
        "min_salary": 450,
        "max_salary": 800,
        "job_level": "Junior",
        "employment_type": "Full-time",
        "work_type": "Hybrid",
        "skills": ["Dart", "Flutter"],
    },
    {
        "title": "UI/UX Designer",
        "description": ["Design intuitive, modern interfaces for our products.", "Run user research and usability testing."],
        "requirements": ["Portfolio of past UI/UX work", "Proficiency with Figma", "Good communication skills"],
        "benefits": ["Health insurance", "Creative freedom", "Flexible hours"],
        "min_salary": 400,
        "max_salary": 700,
        "job_level": "Mid Level",
        "employment_type": "Full-time",
        "work_type": "On-site",
        "skills": ["Communication"],
    },
]

CATEGORY_NAME = "Software Development"
EDUCATION_LEVEL_NAME = "Bachelor's Degree"


async def _find_id_by_name(collection, name: str):
    doc = await collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
    return doc["_id"] if doc else None


async def main():
    company = await company_profiles_collection.find_one({}, sort=[("created_at", 1)])
    if not company:
        print("No company profile found. Log in as an employer in the app and finish company profile setup first, then re-run this script.")
        return
    print(f"Attaching sample jobs to company: {company.get('company_name')} (company_id={company['_id']})")

    category_id = await _find_id_by_name(categories_collection, CATEGORY_NAME)
    education_level_id = await _find_id_by_name(education_levels_collection, EDUCATION_LEVEL_NAME)
    province = await provinces_collection.find_one({"is_active": True})

    missing = []
    if not category_id:
        missing.append(f"category '{CATEGORY_NAME}'")
    if not education_level_id:
        missing.append(f"education level '{EDUCATION_LEVEL_NAME}'")
    if not province:
        missing.append("an active province in job_provinces")
    if missing:
        print("Missing required master data: " + ", ".join(missing))
        print("Run `python -m scripts.seed_master_data` first (and make sure provinces are seeded), then re-run this script.")
        return

    province_id = province["_id"]
    now = datetime.now(timezone.utc)
    created_count = 0

    for job in SAMPLE_JOBS:
        existing = await job_posts_collection.find_one({
            "company_id": company["_id"],
            "title": {"$regex": f"^{job['title']}$", "$options": "i"},
        })
        if existing:
            print(f"  [skip] '{job['title']}' already exists for this company")
            continue

        job_level_id = await _find_id_by_name(job_levels_collection, job["job_level"])
        employment_type_id = await _find_id_by_name(employment_types_collection, job["employment_type"])
        work_type_id = await _find_id_by_name(work_types_collection, job["work_type"])
        skill_ids = []
        for skill_name in job["skills"]:
            skill_id = await _find_id_by_name(skills_collection, skill_name)
            if skill_id:
                skill_ids.append(skill_id)

        if not (job_level_id and employment_type_id and work_type_id):
            print(f"  [skip] '{job['title']}' — missing one of job_level/employment_type/work_type in master data (check seed_master_data.py ran fully)")
            continue

        await job_posts_collection.insert_one({
            "_id": ObjectId(),
            "company_id": company["_id"],
            "category_id": category_id,
            "job_level_id": job_level_id,
            "work_type_id": work_type_id,
            "employment_type_id": employment_type_id,
            "education_level_id": education_level_id,
            "province_id": province_id,
            "district_id": None,
            "required_skills": skill_ids,
            "custom_skills": [],
            "title": job["title"],
            "description": job["description"],
            "requirements": job["requirements"],
            "benefits": job["benefits"],
            "min_salary": job["min_salary"],
            "max_salary": job["max_salary"],
            "salary_period": "per month",
            "is_negotiable": True,
            "headcount": 1,
            "experience": "1 - 3 Years",
            "working_days": "Mon - Fri",
            "working_hours": "8:00 AM - 5:00 PM",
            "specific_schedule": [],
            "closing_date": now + timedelta(days=30),
            "status": "active",
            "created_at": now,
            "updated_at": now,
        })
        created_count += 1
        print(f"  [+] '{job['title']}' created")

    print(f"\nDone. {created_count} job(s) created for {company.get('company_name')}. Open the seeker home screen to see them.")


if __name__ == "__main__":
    asyncio.run(main())
