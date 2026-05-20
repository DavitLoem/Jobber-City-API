from datetime import date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, model_validator


class JobType(str, Enum):
    FIND_JOB = "Find a Job"
    FIND_EMPLOYEE = "Find an Employee"

class CreateAccount(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=50, repr=False)
    job_type_id: str = Field(..., description="Job type ID: 'FIND_JOB' or 'FIND_EMPLOYEE'")

class LoginAccount(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=50, repr=False)



class Forgotpassword(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[0-9]{8,15}$')

    @model_validator(mode='after')
    def check_identity(self):
        if not self.email and not self.phone:
            raise ValueError('Must provide either email or phone')
        return self

class PinCodeVerify(BaseModel):
    email: EmailStr
    pin_code: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")
        
class ResetPassword(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[0-9]{8,15}$')
    new_password: str = Field(..., min_length=8, max_length=72)
    confirm_password: str = Field(..., min_length=8, max_length=72)

    @model_validator(mode='after')
    def validate_passwords(self):
        if not self.email and not self.phone:
            raise ValueError('Must provide email or phone')
        if self.new_password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self

class TokenRespone(BaseModel):
    id: str
    email: EmailStr