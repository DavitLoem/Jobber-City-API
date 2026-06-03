from enum import Enum
from typing import List, Optional  # បន្ថែម Import នេះ
from pydantic import BaseModel, Field, HttpUrl  # បន្ថែម BaseModel និង HttpUrl

class WorkplaceType(str, Enum):
    ONSITE = "Onsite"
    REMOTE = "Remote"
    HYBRID = "Hybrid"

class JobType(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    INTERNSHIP = "Internship"

class Location(str, Enum):
    PHNOM_PENH = "Phnom Penh"
    SIEM_REAP = "Siem Reap"
    PREAH_SIHANOUK = "Preah Sihanouk"
    BATTAMBANG = "Battambang"
    KAMPOT = "Kampot"
    KEP = "Kep"
    KANDAL = "Kandal"
    TAKEO = "Takeo"
    KAMPONG_CHAM = "Kampong Cham"
    KAMPONG_SPEU = "Kampong Speu"
    KAMPONG_THOM = "Kampong Thom"
    KAMPONG_CHHNANG = "Kampong Chhnang"
    PURSAT = "Pursat"
    BANTEAY_MEANCHEY = "Banteay Meanchey"
    SVAY_RIENG = "Svay Rieng"
    PREY_VENG = "Prey Veng"
    KOH_KONG = "Koh Kong"
    KRATIE = "Kratie"
    STUNG_TRENG = "Stung Treng"
    MONDULKIRI = "Mondulkiri"
    RATANAKIRI = "Ratanakiri"
    PREAH_VIHEAR = "Preah Vihear"
    ODDAR_MEANCHEY = "Oddar Meanchey"
    PAILIN = "Pailin"
    TBOUNG_KHMUM = "Tboung Khmum"

class PostJobRequest(BaseModel): 
    job_title: str = Field(..., min_length=3, max_length=100)
    location: Location = Field(..., example="Phnom Penh")
    salary: str = Field(..., example="$1000 - $2000 /month")
    job_type: JobType = Field(..., example="Full-time")
    workplace_type: WorkplaceType = Field(..., example="Onsite")
    job_description: str = Field(..., min_length=10, max_length=1000, example="Job description")
    minimum_qualifications: str = Field(..., min_length=3, max_length=100, example="Minimum qualifications")
    perks_and_benefits: Optional[List[str]] = Field(default=[])
    required_skills: List[str] = Field(..., example=["Figma", "Layout", "Graphic Design"])
    job_level: str = Field(..., example="Associate / Supervisor")
    job_category: str = Field(..., example="IT and Software")
    educational_level: str = Field(..., example="Bachelor's Degree")
    experience_years: str = Field(..., example="1 - 3 Years")
    vacancy_count: int = Field(default=1, ge=1)
    company_website: Optional[HttpUrl] = Field(None, example="https://www.google.com")
    about_company: str = Field(..., min_length=50)
    application_deadline: str = Field(..., example="31 Dec 2025")