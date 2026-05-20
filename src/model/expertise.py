from enum import Enum
from pydantic import BaseModel, Field, field_validator

class Expertise(str, Enum):
    ACCOUNTING_AND_FINANCE = "Accounting and Finance"
    ARCHITECTURE_AND_ENGINEERING = "Architecture and Engineering"
    INFORMATION_TECHNOLOGY_AND_SOFTWARE = "Information Technology and Software"
    MANAGEMENT_AND_CONSULTANCY = "Management and Consultancy"
    MEDIA_DESIGN_AND_CREATIVES = "Media, Design, and Creatives"
    SALES_AND_MARKETING = "Sales and Marketing"
    WRITING_AND_CONTENT = "Writing and Content"

class ExpertisePost(BaseModel):
    expertise: Expertise = Field(..., description="The expertise to add")

    @field_validator('expertise', mode='before')
    @classmethod
    def clean_expertise_string(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            for item in Expertise:
                if item.value.lower() == cleaned.lower():
                    return item.value
        return v

class ExpertiseUpdate(BaseModel):
    expertise: Expertise = Field(..., description="The expertise to update")

    @field_validator('expertise', mode='before')
    @classmethod
    def clean_expertise_string(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            for item in Expertise:
                if item.value.lower() == cleaned.lower():
                    return item.value
        return v