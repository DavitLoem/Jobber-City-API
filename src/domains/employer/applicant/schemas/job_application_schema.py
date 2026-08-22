from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

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
    profile_image_url: Optional[str] = None
    current_position: Optional[str] = None
    
    # ព័ត៌មានពីការដាក់ពាក្យផ្ទាល់
    resume_url: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str
    applied_at: datetime
    job_title: Optional[str] = Field(None, description="ចំណងជើងការងារដែលបេក្ខជននេះបានដាក់ពាក្យ (មានប្រយោជន៍ពេលមើល All Jobs)")


class JobDropdownItem(BaseModel):
    """Schema សម្រាប់ Dropdown ជ្រើសរើស Job នៅលើអេក្រង់ Candidates"""
    job_id: str
    display_name: str
    status: str = "active"


class SeekerDirectoryResponse(BaseModel):
    """Schema សម្រាប់បញ្ជីគណនី Seeker ទាំងអស់ក្នុងប្រព័ន្ធ (សម្រាប់ Employer ជ្រើសរើសចាប់ផ្ដើម Chat ថ្មី)"""
    seeker_user_id: str = Field(..., description="ID របស់គណនី Seeker")
    first_name: str
    last_name: str
    profile_image_url: Optional[str] = None
    current_position: Optional[str] = None
    has_applied_to_you: bool = Field(False, description="ធ្លាប់បានដាក់ពាក្យស្នើសុំការងារមកក្រុមហ៊ុននេះ ឬអត់")


class SeekerDirectoryPage(BaseModel):
    """Schema សម្រាប់លទ្ធផលបញ្ជី Seeker ដែលមាន Pagination"""
    items: list[SeekerDirectoryResponse]
    total: int
    page: int
    limit: int
    has_more: bool