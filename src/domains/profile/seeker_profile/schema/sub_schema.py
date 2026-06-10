from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

# ==========================================
# 1. បទពិសោធន៍ការងារ (Work Experiences)
# ==========================================
class ExperienceRequest(BaseModel):
    job_title: str = Field(..., min_length=2, example="Software Engineer")
    company_name: str = Field(..., min_length=2, example="Tech Corp")
    start_date: date = Field(..., example="2020-01-15")
    end_date: Optional[date] = Field(None, description="ទុក None បើកំពុងធ្វើការបច្ចុប្បន្ន")
    is_current_job: bool = Field(default=False)
    description: Optional[str] = Field(None, example="អភិវឌ្ឍន៍ប្រព័ន្ធ Backend...")

class ExperienceResponse(ExperienceRequest):
    id: str = Field(description="ID សម្រាប់ចំណាំបទពិសោធន៍មួយនេះ (Generate ដោយ Backend)")

# ==========================================
# 2. ប្រវត្តិការសិក្សា (Educations)
# ==========================================
class EducationRequest(BaseModel):
    school_name: str = Field(..., min_length=2, example="Norton University")
    degree: str = Field(..., example="Bachelor's Degree")
    field_of_study: Optional[str] = Field(None, example="Computer Science")
    start_date: date = Field(..., example="2018-10-01")
    end_date: Optional[date] = Field(None, example="2022-07-20")

class EducationResponse(EducationRequest):
    id: str

# ==========================================
# 3. ការបណ្តុះបណ្តាល និងវគ្គខ្លី (Trainings)
# ==========================================
class TrainingRequest(BaseModel):
    course_name: str = Field(..., min_length=2, example="AWS Cloud Practitioner")
    institution: str = Field(..., example="AWS Academy")
    start_date: Optional[date] = Field(None)
    end_date: Optional[date] = Field(None)
    description: Optional[str] = Field(None)
    certificate_url: Optional[str] = Field(None)

class TrainingResponse(TrainingRequest):
    id: str

# ==========================================
# 4. ភាសា (Languages)
# ==========================================
class LanguageRequest(BaseModel):
    language: str = Field(..., example="English")
    proficiency: str = Field(..., example="Fluent", description="ឧ. Basic, Conversational, Fluent, Native")

class LanguageResponse(LanguageRequest):
    id: str