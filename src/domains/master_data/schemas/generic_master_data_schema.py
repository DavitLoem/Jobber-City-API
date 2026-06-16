from typing import Optional
from pydantic import BaseModel, Field

class GenericMasterDataCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="ឈ្មោះទិន្នន័យគោល")
    order: Optional[int] = Field(default=0, description="លេខរៀងសម្រាប់តម្រៀបពេលបង្ហាញ")
    is_active: Optional[bool] = Field(default=True, description="កំណត់ថាបើកឱ្យប្រើ ឬបិទ")

class GenericMasterDataUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    order: Optional[int] = Field(None)
    is_active: Optional[bool] = Field(None)

# ==========================================
# ផ្នែក RESPONSE (សម្រាប់បោះត្រឡប់ទៅឱ្យ Admin ឬ Mobile App វិញ)
# ==========================================
class GenericMasterDataResponse(BaseModel):
    id: str
    name: str
    order: int
    is_active: bool

    class Config:
        json_schema_extra = {
            "example": {
                "id": "64f1a2b3...",
                "name": "Full-time",
                "order": 1,
                "is_active": True
            }
        }