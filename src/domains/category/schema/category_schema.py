from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CategoryRequest(BaseModel):
    # Field(...) មានន័យថា Required ដាច់ខាតត្រូវតែមាន
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=100, 
        description="ឈ្មោះប្រភេទការងារ (ឧទាហរណ៍: Software Development)"
    )
    
    icon_url: Optional[str] = Field(
        default=None, 
        description="តំណភ្ជាប់ទៅកាន់រូបតំណាង (Icon) របស់ Category នេះ"
    )
    
    sort_order: Optional[int] = Field(
        default=99, 
        ge=0, 
        description="លំដាប់លេខរៀងសម្រាប់បង្ហាញ (លេខតូចនៅមុន)"
    )
    
    is_active: Optional[bool] = Field(
        default=True, 
        description="កំណត់ស្ថានភាពបើកដំណើរការ ឬបិទ"
    )

class CategoryResponse(BaseModel):
    id: str = Field(description="ID របស់ប្រភេទការងារ")
    name: str
    icon_url: Optional[str] = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    