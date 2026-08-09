from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict

# ==========================================
# 📍 REQUEST SCHEMAS (ទិន្នន័យដែល Frontend បញ្ជូនមក Backend)
# ==========================================

class ApplyJobRequest(BaseModel):
    """Schema សម្រាប់ Seeker ប្រើពេលចុចដាក់ពាក្យ (Apply Job)"""
    cover_letter: Optional[str] = Field(None, description="សារខ្លីៗបញ្ចុះបញ្ចូលក្រុមហ៊ុន")
    resume_url: Optional[str] = Field(None, description="Link របស់ CV (បើមិនបញ្ជូនមក វានឹងយកពី Profile ដោយស្វ័យប្រវត្តិ)")

class UpdateApplicationStatus(BaseModel):
    """Schema សម្រាប់ Employer ប្រើពេលប្តូរស្ថានភាពបេក្ខជន"""
    status: str = Field(..., description="ឧទាហរណ៍: pending, reviewed, shortlisted, interview, hired, rejected")


# ==========================================
# 📍 RESPONSE SCHEMAS (ទិន្នន័យដែល Backend បោះត្រឡប់ទៅ Frontend)
# ==========================================

class ApplicantResponse(BaseModel):
    """Schema សម្រាប់បោះបញ្ជីអ្នកដាក់ពាក្យ ទៅឱ្យ Employer មើល (បង្ហាញលើ Dashboard)"""
    application_id: str = Field(..., description="ID របស់តារាង Job Application")
    seeker_user_id: str = Field(..., description="ID របស់គណនី Seeker")
    
    # ព័ត៌មានដែល Join ចេញពី Seeker Profile
    first_name: str
    last_name: str
    job_title: str
    profile_image_url: Optional[str] = None
    current_position: Optional[str] = None
    
    skills: List[str] = []
    years_of_experience: int = 0
    
    # ព័ត៌មានពីការដាក់ពាក្យផ្ទាល់
    resume_url: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str
    applied_at: datetime
    
class SeekerApplicationResponse(BaseModel):
    """Schema សម្រាប់បោះព័ត៌មានលម្អិតនៃការដាក់ពាក្យ ទៅឱ្យ Seeker"""
    application_id: str
    job_id: str
    company_id: str
    
    # ព័ត៌មានដែល Join ចេញពី Job Post និង Company
    job_title: str
    company_name: str
    company_logo: Optional[str] = None
    
    # ព័ត៌មានពីការដាក់ពាក្យផ្ទាល់
    resume_url: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str
    applied_at: datetime
    updated_at: datetime
    
    # 🟢 Field ថ្មីសម្រាប់ Detail View
    status_history: List[Dict] = []
    interview_schedule: Optional[Dict] = None
    feedback: Optional[str] = ""
    
class JobDropdownItemResponse(BaseModel):
    job_id: str
    display_name: str
    status: str