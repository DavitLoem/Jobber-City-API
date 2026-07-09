from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class JobFeedResponse(BaseModel):
    """ទម្រង់ទិន្នន័យសម្រាប់បង្ហាញនៅលើ Job Card (Home Screen)"""
    id: str
    
    # ព័ត៌មានការងារ
    title: str
    min_salary: float
    max_salary: float
    salary_period: str
    
    # ព័ត៌មានដែល Join មកពី Company
    company_name: str
    logo_url: Optional[str] = None
    
    # ព័ត៌មានដែល Join មកពី Master Data (បំប្លែងរួចជាស្រេចពី Backend)
    location: str = Field(..., description="ឧ. Russey Keo, Phnom Penh")
    employment_type: str = Field(..., description="ឧ. Full Time")
    work_type: str = Field(..., description="ឧ. Remote ឬ On-site")
    
    # គ្រប់គ្រងប្រព័ន្ធ
    created_at: datetime
    
    # សម្រាប់មុខងារ Bookmark (ថ្ងៃក្រោយ)
    is_saved: bool = Field(False, description="បញ្ជាក់ថា Seeker បានចុច Save ទុកឬអត់")
    
    # សម្រាប់មុខងារ Recommendation (ថ្ងៃក្រោយ)
    match_percentage: Optional[int] = Field(None, description="ភាគរយស័ក្តិសម (ឧ. 80)")