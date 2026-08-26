from pydantic import BaseModel
from typing import List, Optional

# ── ទម្រង់ទិន្នន័យសម្រាប់កាតនីមួយៗ ──
class KPITrendModel(BaseModel):
    value: int
    trend: Optional[float] = None
    trend_label: str

# ── ទម្រង់ទិន្នន័យរួមសម្រាប់ API (Response) ──
class KPISummaryResponse(BaseModel):
    total_users: KPITrendModel
    pending_verifications: KPITrendModel
    active_jobs: KPITrendModel
    total_applications: KPITrendModel
    
class GrowthSeries(BaseModel):
    name: str
    data: List[int]

class PlatformGrowthResponse(BaseModel):
    categories: List[str]  # ឧ. ["Jan", "Feb", "Mar", ...]
    series: List[GrowthSeries]

# ── 3. Jobs by Category (Donut Chart) ──
class JobsCategoryResponse(BaseModel):
    labels: List[str]      # ឧ. ["Technology", "Marketing", ...]
    series: List[int]      # ឧ. [450, 250, ...]
    total_active_jobs: int