from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class SeekerCoreProfileUpdateRequest(BaseModel):
    """Schema សម្រាប់ទទួលទិន្នន័យ Update ព័ត៌មានគោលពី Mobile App"""
    
    # 🎯 ១. ព័ត៌មានផ្ទាល់ខ្លួន (Personal Info)
    first_name: Optional[str] = Field(None, min_length=1, example="Sok")
    last_name: Optional[str] = Field(None, min_length=1, example="San")
    date_of_birth: Optional[date] = Field(None, example="1998-05-20")
    gender: Optional[str] = Field(None, example="Male")
    marital_status: Optional[str] = Field(None, example="Single")
    nationality: Optional[str] = Field(None, example="Cambodian")
    
    # 🎯 ២. ទំនាក់ទំនង និង ឋានៈ (Contact & Headline)
    current_position: Optional[str] = Field(None, example="Mobile App Developer")
    email: Optional[str] = Field(None, example="soksan@email.com")
    phone_number: Optional[str] = Field(None, example="012345678")

    # 🎯 ៣. អាសយដ្ឋាន (Location)
    province_id: Optional[str] = Field(None, description="ID របស់ខេត្ត/ក្រុង")
    district_id: Optional[str] = Field(None, description="ID របស់ស្រុក/ខណ្ឌ")
    commune: Optional[str] = Field(None, example="Sangkat Boeng Keng Kang 1")
    village: Optional[str] = Field(None, example="Village 1")
    street: Optional[str] = Field(None, example="Street 282")
    house_no: Optional[str] = Field(None, example="#12A")

    # 🎯 ៤. ចំណង់ចំណូលចិត្ត និងការពិពណ៌នា (Preferences & Biography)
    biography: Optional[str] = Field(None, description="ការពិពណ៌នាសង្ខេបអំពីខ្លួនឯង")
    expected_salary_min: Optional[int] = Field(None, ge=0, example=300)
    expected_salary_max: Optional[int] = Field(None, ge=0, example=800)
    job_type_preferences: Optional[List[str]] = Field(None, example=["Full-time", "Freelance"])
    expertise_category_ids: Optional[List[str]] = Field(None, description="បញ្ជី ID ប្រភេទការងារដែលគាត់ជំនាញ")
    
    # 🎯 ៥. ជំនាញ និង តំណភ្ជាប់ (Skills & Links)
    skills: Optional[List[str]] = Field(None, example=["Python", "FastAPI", "Flutter"])
    portfolio_url: Optional[str] = Field(None, example="https://myportfolio.com")
    linkedin_url: Optional[str] = Field(None, example="https://linkedin.com/in/soksan")
    
    onboarding_completed: Optional[bool] = Field(None, description="កំណត់ថាតើគាត់ឆ្លងកាត់ការរើសទិន្នន័យលើកដំបូងរួចរាល់ឬនៅ")

class SeekerProfileResponse(BaseModel):
    """Schema សម្រាប់បោះទិន្នន័យ Profile ទាំងមូលទៅកាន់ Mobile App វិញ"""
    id: str = Field(..., alias="_id")
    user_id: str
    
    profile_image_url: Optional[str] = None
    profile_completion_percentage: int
    onboarding_completed: bool = False
    
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    current_position: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    
    province_id: Optional[str] = None
    district_id: Optional[str] = None
    commune: Optional[str] = None
    village: Optional[str] = None
    street: Optional[str] = None
    house_no: Optional[str] = None

    biography: Optional[str] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None
    job_type_preferences: List[str] = []
    expertise_category_ids: List[str] = []
    skills: List[str] = []

    resume_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    # យើងប្រើ list ទទេរសម្រាប់ array sub-documents ដែលមិនទាន់មានទិន្នន័យ
    experiences: list = []
    educations: list = []
    trainings: list = []
    languages: list = []
    
    # Configuration សម្រាប់ Pydantic ជំនាន់ v2
    class Config:
        populate_by_name = True