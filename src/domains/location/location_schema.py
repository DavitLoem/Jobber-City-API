from pydantic import BaseModel, Field
from typing import Optional

# ==========================================
# 1. REQUEST SCHEMAS (មាន Validation តឹងរ៉ឹង)
# ==========================================

class ProvinceRequest(BaseModel):
    name_en: str = Field(..., min_length=2, max_length=100, description="ឈ្មោះខេត្តជាភាសាអង់គ្លេស")
    name_km: Optional[str] = Field(default=None, max_length=100, description="ឈ្មោះជាភាសាខ្មែរ (អាចមិនដាក់ក៏បាន)")
    sort_order: Optional[int] = Field(default=99, ge=0, description="លេខរៀងសម្រាប់បង្ហាញ (មិនអាចអវិជ្ជមាន)")
    is_active: Optional[bool] = Field(default=True, description="ស្ថានភាពបិទ ឬបើក")

class DistrictRequest(BaseModel):
    province_id: str = Field(..., min_length=24, max_length=24, description="លេខសម្គាល់ខេត្ត (ObjectId)")
    name_en: str = Field(..., min_length=2, max_length=100, description="ឈ្មោះស្រុកជាភាសាអង់គ្លេស")
    name_km: Optional[str] = Field(default=None, min_length=2, max_length=100, description="ឈ្មោះស្រុកជាភាសាខ្មែរ")
    sort_order: Optional[int] = Field(default=99, ge=0)
    is_active: Optional[bool] = Field(default=True)

# ==========================================
# 2. RESPONSE SCHEMAS (សម្រាប់បោះទិន្នន័យទៅឱ្យ Mobile App)
# ==========================================

class ProvinceResponse(BaseModel):
    id: str
    name_km: str
    name_en: str
    sort_order: int
    is_active: bool

class DistrictResponse(BaseModel):
    id: str
    province_id: str
    name_km: str
    name_en: str
    sort_order: int
    is_active: bool