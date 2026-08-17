from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ── ១. ទម្រង់ទិន្នន័យសម្រាប់កាតទាំង ៤ (Overview Stats) ──
class OverviewStatsModel(BaseModel):
    jobs_posted: int = 0
    jobs_posted_trend: str = "0"          # ឧទាហរណ៍: "+3" ឬ "-1"
    
    total_applications: int = 0
    applications_trend: str = "0"
    
    interviews: int = 0
    interviews_trend: str = "0"
    
    hired: int = 0
    hired_trend: str = "0"

# ── ២. ទម្រង់ទិន្នន័យសម្រាប់របារ Applicant Pipeline ──
class PipelineStatsModel(BaseModel):
    active_candidates: int = 0
    screening: int = 0
    review: int = 0
    interview: int = 0
    offer: int = 0

# ── ៣. ទម្រង់ទិន្នន័យសម្រាប់បេក្ខជនថ្មីៗ (Recent Applicants) ──
class RecentApplicantModel(BaseModel):
    applicant_id: str
    seeker_id: str
    name: str
    avatar_url: str
    job_title: str
    status: str
    applied_at: datetime
    rating: Optional[float] = 0.0

# ── ៤. ទម្រង់ទិន្នន័យមេ (Main Dashboard Response) ──
class EmployerDashboardResponse(BaseModel):
    overview: OverviewStatsModel
    pipeline: PipelineStatsModel
    recent_applicants: List[RecentApplicantModel]