from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CategoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Plumbing")
    icon_url: Optional[str] = None
    sort_order: Optional[int] = Field(default=99 , ge=0, example=1)
    is_active: Optional[bool] = Field(default=True, example=True)

class CategoryResponse(BaseModel):
    id: str
    name: str
    icon_url: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime
    is_active: bool