from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ── 1. Schema សម្រាប់ KPI ──
class SeekerKpiResponse(BaseModel):
    total_seekers: int
    active: int
    suspended: int
    banned: int

# ── 2. Schema សម្រាប់តារាងបញ្ជីអ្នកស្វែងរកការងារ ──
class AdminSeekerListItem(BaseModel):
    user_id: str
    full_name: str
    avatar_url: Optional[str]
    current_position: str
    
    email: str
    phone_number: str
    
    applications_count: int
    
    status: str # 'active', 'suspended', ឬ 'banned'
    created_at: datetime

class AdminSeekerListResponse(BaseModel):
    items: List[AdminSeekerListItem]
    total: int
    page: int
    limit: int