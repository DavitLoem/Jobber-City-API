from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# ==========================================
# ផ្នែក REQUEST (សម្រាប់ Create)
# ==========================================
class JobPostCreate(BaseModel):
    # ព័ត៌មានស្នូល
    title: str = Field(..., min_length=3, max_length=150, description="ចំណងជើងការងារ")
    description: List[str] = Field(..., min_length=1, description="ការពិពណ៌នាការងារ (Array នៃចំណុចៗ)")
    requirements: List[str] = Field(..., min_length=1, description="លក្ខខណ្ឌជ្រើសរើស (Array នៃចំណុចៗ)")
    benefits: List[str] = Field(..., min_length=1, description="អត្ថប្រយោជន៍ទទួលបាន (Array នៃចំណុចៗ)")
    
    # ប្រាក់ខែ & ចំនួន
    min_salary: float = Field(0, description="ប្រាក់ខែគោល (0 បើចង់លាក់)")
    max_salary: float = Field(0, description="ប្រាក់ខែខ្ពស់បំផុត")
    salary_period: str = Field(..., description="ឧ. per month, per hour")
    is_negotiable: bool = Field(True, description="អាចចរចាបានឬអត់")
    headcount: int = Field(1, ge=1, description="ចំនួនអ្នកដែលត្រូវការ (ត្រូវធំជាងឬស្មើ ១)")
    
    # លក្ខខណ្ឌ & ពេលវេលា
    experience: str = Field(..., description="បទពិសោធន៍ (ឧ. 1 - 3 Years)")
    working_days: str = Field(..., description="ថ្ងៃធ្វើការ (ឧ. Mon - Sat)")
    working_hours: str = Field(..., description="ម៉ោងធ្វើការ (ឧ. 8:00 AM - 5:00 PM)")
    specific_schedule: Optional[List[dict]] = Field(
        None, description="កាលវិភាគពិសេស (List of {day, hours})"
    )
    
    # Foreign Keys (Master Data)
    category_id: str = Field(..., description="ID ប្រភេទការងារ")
    job_level_id: str = Field(..., description="ID កម្រិតការងារ (Junior, Senior...)")
    work_type_id: str = Field(..., description="ID របៀបធ្វើការ (Remote, On-site...)")
    employment_type_id: str = Field(..., description="ID ប្រភេទកិច្ចសន្យា (Full-time...)")
    education_level_id: str = Field(..., description="ID កម្រិតវប្បធម៌")
    required_skills: List[str] = Field(..., min_length=1, description="List of skill_ids")
    province_id: str = Field(..., description="ID ខេត្ត/ក្រុង")
    district_id: Optional[str] = Field(None, description="ID ស្រុក/ខណ្ឌ (មិនកាតព្វកិច្ច)")
    
    # គ្រប់គ្រងប្រព័ន្ធ
    closing_date: datetime = Field(..., description="ថ្ងៃផុតកំណត់ឈប់ទទួលពាក្យ")


# ==========================================
# ផ្នែក REQUEST (សម្រាប់ Update)
# ==========================================
class JobPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[List[str]] = Field(None, min_length=1)
    requirements: Optional[List[str]] = Field(None, min_length=1)
    benefits: Optional[List[str]] = Field(None, min_length=1)
    
    min_salary: Optional[float] = Field(None)
    max_salary: Optional[float] = Field(None)
    salary_period: Optional[str] = Field(None)
    is_negotiable: Optional[bool] = Field(None)
    headcount: Optional[int] = Field(None, ge=1)
    
    experience: Optional[str] = Field(None)
    working_days: Optional[str] = Field(None)
    working_hours: Optional[str] = Field(None)
    specific_schedule: Optional[List[dict]] = Field(None)
    
    category_id: Optional[str] = Field(None)
    job_level_id: Optional[str] = Field(None)
    work_type_id: Optional[str] = Field(None)
    employment_type_id: Optional[str] = Field(None)
    education_level_id: Optional[str] = Field(None)
    required_skills: Optional[List[str]] = Field(None, min_length=1)
    province_id: Optional[str] = Field(None)
    district_id: Optional[str] = Field(None)
    
    closing_date: Optional[datetime] = Field(None)
    status: Optional[str] = Field(None, description="ឧ. active, closed, draft")


# ==========================================
# ផ្នែក RESPONSE (បោះត្រឡប់ទៅ UI)
# ==========================================
class JobPostResponse(BaseModel):
    id: str
    company_id: str
    title: str
    description: List[str]
    requirements: List[str]
    benefits: List[str]
    min_salary: float
    max_salary: float
    salary_period: str
    is_negotiable: bool
    headcount: int
    experience: str
    working_days: str
    working_hours: str
    specific_schedule: Optional[List[dict]]
    category_id: str
    job_level_id: str
    work_type_id: str
    employment_type_id: str
    education_level_id: str
    required_skills: List[str]
    province_id: str
    district_id: Optional[str]
    closing_date: datetime
    status: str
    created_at: datetime
    updated_at: datetime