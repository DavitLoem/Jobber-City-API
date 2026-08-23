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
    cover_letter_url: Optional[str] = None
    cover_letter_filename: Optional[str] = None

class UpdateApplicationStatus(BaseModel):
    """Schema សម្រាប់ Employer ប្រើពេលប្តូរស្ថានភាពបេក្ខជន"""
    status: str = Field(..., description="ឧទាហរណ៍: pending, reviewed, shortlisted, interview, hired, rejected")
    
    # 🟢 បន្ថែម Field ទាំង ២ នេះ ដើម្បីឱ្យ API ព្រមទទួលយកទិន្នន័យពី Flutter
    interview_schedule: Optional[Dict] = Field(None, description="ព័ត៌មានលម្អិតពេលហៅសម្ភាសន៍")
    feedback: Optional[str] = Field(None, description="មតិកែលម្អពេល Reject")


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
    resume_filename: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str
    applied_at: datetime
    
    # 🟢 បន្ថែម Field ទាំង ២ នេះ ដើម្បីឱ្យ API ព្រមបោះទិន្នន័យនេះទៅកាន់ Flutter វិញ
    interview_schedule: Optional[Dict] = None
    feedback: Optional[str] = None
    
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
    resume_filename: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str
    applied_at: datetime
    updated_at: datetime
    
    # Field ថ្មីសម្រាប់ Detail View
    status_history: List[Dict] = []
    interview_schedule: Optional[Dict] = None
    feedback: Optional[str] = ""
    
class JobDropdownItemResponse(BaseModel):
    job_id: str
    display_name: str
    status: str
    
class ApplicantStatusSummaryResponse(BaseModel):
    """Schema សម្រាប់បោះចំនួនបេក្ខជនសរុបក្នុង Status នីមួយៗទៅឱ្យ UI"""
    all: int = 0
    pending: int = 0
    shortlisted: int = 0
    interview: int = 0
    hired: int = 0
    rejected: int = 0
    
# 🟢 បន្ថែម Schema នេះសម្រាប់ទទួល Data ជា Array ពី Flutter
class BulkUpdateApplicationStatus(BaseModel):
    """Schema សម្រាប់ Employer ប្រើពេលប្តូរស្ថានភាពបេក្ខជនច្រើននាក់ព្រមគ្នា (Bulk Action)"""
    application_ids: List[str] = Field(..., description="បញ្ជី ID របស់បេក្ខជនទាំងអស់ដែលត្រូវបានជ្រើសរើស")
    status: str = Field(..., description="ស្ថានភាពថ្មី (ឧទាហរណ៍: shortlisted, interview, rejected)")
    
    interview_schedule: Optional[Dict] = Field(None, description="ព័ត៌មានលម្អិតពេលហៅសម្ភាសន៍")
    feedback: Optional[str] = Field(None, description="មតិកែលម្អ (សម្រាប់ករណី Reject)")