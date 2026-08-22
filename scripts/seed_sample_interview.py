"""
Creates one sample job application (seeker -> employer's job) and one
sample interview scheduled ~3 minutes from now, so the "Interviews" screen
has real data to show immediately on both the employer's and seeker's
devices, and the "Join Interview" button is joinable right away (the join
window opens 10 minutes before the scheduled time).

Prerequisites (run once, in order):
    1. python -m scripts.seed_master_data
    2. python -m scripts.seed_sample_job
       (needs at least one job post under your employer's company)
    3. Have at least one seeker account created in the app.

Run from the backend project root, with your venv active:

    cd Jobber-City-API
    source .venv/bin/activate
    python -m scripts.seed_sample_interview

Safe to re-run — always creates a fresh interview (each run is a new test
case), but re-uses the same application if one already exists between that
seeker and job.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from src.core.mongo import (
    company_profiles_collection,
    job_posts_collection,
    job_applications_collection,
    users_collection,
    interviews_collection,
)
from src.domains.employer.applicant.models.job_application_model import JobApplicationModel
from src.domains.interview.models.interview_model import InterviewModel, build_meeting_url


async def main():
    company = await company_profiles_collection.find_one({}, sort=[("created_at", 1)])
    if not company:
        print("No company profile found. Log in as an employer in the app and finish company profile setup first.")
        return

    job = await job_posts_collection.find_one({"company_id": company["_id"]}, sort=[("created_at", 1)])
    if not job:
        print("No job post found for this company. Run `python -m scripts.seed_sample_job` first.")
        return

    seeker = await users_collection.find_one({"role": "seeker", "is_active": True}, sort=[("created_at", 1)])
    if not seeker:
        print("No seeker account found. Create/register a seeker account in the app first.")
        return

    print(f"Employer company: {company.get('company_name')}")
    print(f"Job post: {job.get('title')}")
    print(f"Seeker: {seeker.get('first_name')} {seeker.get('last_name')} ({seeker['_id']})")

    # 1. Get-or-create the job application (needed so the interview can link
    #    to a real application_id, matching how a real employer would do it
    #    from the candidate detail screen).
    application = await job_applications_collection.find_one({
        "job_id": job["_id"],
        "seeker_user_id": seeker["_id"],
    })
    if application:
        print(f"  [skip] Application already exists ({application['_id']})")
    else:
        model = JobApplicationModel(
            job_id=job["_id"],
            company_id=company["_id"],
            seeker_user_id=seeker["_id"],
            cover_letter="Sample application created for testing the interview feature.",
            status="shortlisted",
        )
        new_app = model.to_create_dict()
        await job_applications_collection.insert_one(new_app)
        application = new_app
        print(f"  [+] Application created ({application['_id']})")

    # 2. Create the interview, scheduled 3 minutes out — inside the 10-minute
    #    join window immediately, but still technically "in the future" so it
    #    passes backend validation.
    scheduled_at = datetime.now(timezone.utc) + timedelta(minutes=3)
    interview_model = InterviewModel(
        employer_id=company["user_id"],
        seeker_id=seeker["_id"],
        company_id=company["_id"],
        scheduled_at=scheduled_at,
        duration_minutes=30,
        job_id=job["_id"],
        application_id=application["_id"],
        notes="Sample interview created for testing — feel free to cancel/reschedule.",
    )
    new_interview = interview_model.to_create_dict()
    await interviews_collection.insert_one(new_interview)

    print(f"\n[+] Interview scheduled for {scheduled_at.strftime('%H:%M UTC')} (in ~3 minutes)")
    print(f"    Meeting link: {build_meeting_url(new_interview['room_name'])}")
    print("    Open 'Interviews' on both the employer and seeker devices — it'll show under 'Upcoming'.")
    print("    'Join Interview' will work immediately (join window opens 10 min before the scheduled time).")


if __name__ == "__main__":
    asyncio.run(main())
