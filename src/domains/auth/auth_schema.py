from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, ConfigDict, Field, model_validator

# 1. កំណត់ប្រភេទ Role ឱ្យច្បាស់លាស់ (ជំនួស JobType ចាស់)
class RoleEnum(str, Enum):
    EMPLOYEE = "seeker"
    EMPLOYER = "employer"
    # ADMIN = "admin"

# ==========================================
# ផ្នែក REQUEST SCHEMAS (ទិន្នន័យដែល Client បញ្ជូនមក)
# ==========================================

# Schema សម្រាប់ចុះឈ្មោះ (Mobile App)
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr # តម្រូវឱ្យមាន Email ព្រោះយើងប្រើ Email សម្រាប់ OTP
    phone_number: Optional[str] = Field(None, max_length=20, description="Optional contact number")
    password: str = Field(..., min_length=8, max_length=50, repr=False)
    role: RoleEnum = Field(..., description="Role: 'seeker' or 'employer'")

    # 🎯 នេះគឺជាការកំណត់ Example Value នៅក្នុង Swagger UI
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Sok Dara",
                "email": "dara.sok@example.com",
                "phone_number": "012345678",
                "password": "StrongPassword123!",
                "role": "seeker" 
            }
        }
    )

# Schema សម្រាប់ Login ធម្មតា
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, repr=False)

# 🎯 ថ្មី: Schema សម្រាប់អ្នកចុះឈ្មោះ ឬ Login តាម Google
class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., description="Token received from Google Sign-In SDK")
    role: RoleEnum = Field(default=RoleEnum.EMPLOYEE, description="Role: 'seeker' or 'employer'")

# Schema សម្រាប់សុំកូដ OTP ពេលភ្លេចពាក្យសម្ងាត់
class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address associated with the account")
    
class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address associated with the account")
    otp_code: str = Field(..., min_length=6, max_length=6, description="OTP code sent to the user's email")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")

    @model_validator(mode='after')
    def check_passwords_match(self) -> 'ResetPasswordRequest':
        if self.new_password != self.confirm_password:
            raise ValueError("ពាក្យសម្ងាត់ថ្មី និងការបញ្ជាក់ពាក្យសម្ងាត់មិនត្រូវគ្នាទេ")
        return self

# Schema សម្រាប់ផ្ទៀងផ្ទាត់កូដ OTP (ប្តូរពី 4 ខ្ទង់ ទៅ 6 ខ្ទង់ដើម្បីសុវត្ថិភាពខ្ពស់)
class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
 
# ​For admin   
class OTPChallengeResponse(BaseModel):
    requires_otp: bool
    email: str
    message: str
    
class ResendOTPRequest(BaseModel):
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")
    confirm_password: str = Field(..., description="Confirm new password")

    @model_validator(mode='after')
    def check_passwords_match(self) -> 'ChangePasswordRequest':
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirm password do not match")
        if self.old_password == self.new_password:
            raise ValueError("New password cannot be the same as the current password")
        return self


# ==========================================
# ផ្នែក RESPONSE SCHEMAS (ទិន្នន័យដែល API បោះត្រឡប់ទៅវិញ)
# ==========================================

# Schema សម្រាប់បង្ហាញព័ត៌មាន User (មិនបោះ Password ទៅវិញទេ)
class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    avatar_url: Optional[str] = None
    is_profile_completed: bool

# Schema សម្រាប់ JWT Tokens (បែងចែក Access និង Refresh)
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse # បោះទិន្នន័យ User ត្រឡប់ទៅឱ្យ App តែម្តង ដើម្បីកុំឱ្យ App ហៅ API ម្តងទៀត
    
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh Token ដែលទទួលបានពេល Login")