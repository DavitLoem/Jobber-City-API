from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ── 1. Schema សម្រាប់ KPI ──
class CompanyKpiResponse(BaseModel):
    total_companies: int
    pending_approval: int
    verified: int
    rejected: int

# ── 2. Schema សម្រាប់តារាងបញ្ជីក្រុមហ៊ុន ──
class AdminCompanyListItem(BaseModel):
    company_id: str
    company_name: str
    logo_url: Optional[str]
    province_id: Optional[str]
    
    industry_name: str # ទាញពី Industry Collection
    
    owner_name: str    # ទាញពី User Collection
    owner_email: str   # ទាញពី User Collection
    
    status: str
    is_verified: bool
    created_at: datetime

class AdminCompanyListResponse(BaseModel):
    items: List[AdminCompanyListItem]
    total: int
    page: int
    limit: int