from pydantic import BaseModel, Field
from datetime import date
from pydantic import EmailStr

class FillProfile(BaseModel):
    fullname: str = Field(..., max_length=100)
    nickname: str = Field(..., max_length=50)
    date_of_birth: date 
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?[0-9]{8,15}$')
    gender: str
  