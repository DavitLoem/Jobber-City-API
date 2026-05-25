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

# 🎯 ទុកតែ email មួយមុខគត់សម្រាប់ Forgot Password
class Forgotpassword(BaseModel):
    email: EmailStr

class PinCodeVerify(BaseModel):
    email: EmailStr
    pin_code: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")
        
# 🎯 ទុកតែ email និងលុប validation phone ចេញ
class ResetPassword(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=8, max_length=72)
    confirm_password: str = Field(..., min_length=8, max_length=72)

    @model_validator(mode='after')
    def validate_passwords(self):
        if self.new_password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self

class TokenRespone(BaseModel):
    id: str
    email: EmailStr