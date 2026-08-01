from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class JobFeedResponse(BaseModel):
    """ទម្រង់ទិន្នន័យសម្រាប់បង្ហាញនៅលើ Job Card និង Detail Screen"""
    id: str
    
    # ព័ត៌មានការងារ (Card Level)[cite: 13]
    title: str
    min_salary: float
    max_salary: float
    salary_period: str
    
    # 🎯 ព័ត៌មានលម្អិត (Detail Level ដែលបានបន្ថែមថ្មី)[cite: 17]
    description: List[str] = Field(default_factory=list, description="ការពិពណ៌នាការងារ")
    requirements: List[str] = Field(default_factory=list, description="លក្ខខណ្ឌជ្រើសរើស")
    benefits: List[str] = Field(default_factory=list, description="អត្ថប្រយោជន៍ទទួលបាន")
    experience: str = Field("", description="បទពិសោធន៍ទាមទារ")
    working_days: str = Field("", description="ថ្ងៃធ្វើការ")
    working_hours: str = Field("", description="ម៉ោងធ្វើការ")
    is_negotiable: bool = Field(True, description="អាចចរចាប្រាក់ខែបានឬអត់")
    headcount: int = Field(1, description="ចំនួនបុគ្គលិកដែលត្រូវការ")
    closing_date: Optional[datetime] = Field(None, description="ថ្ងៃផុតកំណត់ឈប់ទទួលពាក្យ")
    
    # ព័ត៌មានដែល Join មកពី Company[cite: 13]
    company_name: str
    logo_url: Optional[str] = None
    
    # ព័ត៌មានដែល Join មកពី Master Data[cite: 13]
    location: str = Field(..., description="ឧ. Russey Keo, Phnom Penh")
    employment_type: str = Field(..., description="ឧ. Full Time")
    work_type: str = Field(..., description="ឧ. Remote ឬ On-site")
    
    # គ្រប់គ្រងប្រព័ន្ធ[cite: 13]
    created_at: datetime
    is_saved: bool = Field(False, description="បញ្ជាក់ថា Seeker បានចុច Save ទុកឬអត់")
    match_percentage: Optional[int] = Field(None, description="ភាគរយស័ក្តិសម (ឧ. 80)")