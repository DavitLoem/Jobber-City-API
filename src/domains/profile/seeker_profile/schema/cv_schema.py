from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CVTemplateInfo(BaseModel):
    id: str
    name: str
    description: str


class GenerateCVRequest(BaseModel):
    template_id: str = "modern"


class GenerateCVResponse(BaseModel):
    cv_url: str
    template_id: str
    generated_at: datetime


class CurrentCVResponse(BaseModel):
    cv_url: Optional[str] = None
    template_id: Optional[str] = None
    generated_at: Optional[datetime] = None
