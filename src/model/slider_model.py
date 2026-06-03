from pydantic import BaseModel, Field
from typing import Optional

class SliderRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    button_text: str = Field("Read more", max_length=30)
    link_url: Optional[str] = Field(None, example="/promotion/job-tips")
    order: int = Field(0, ge=0)
    is_active: bool = Field(True)


