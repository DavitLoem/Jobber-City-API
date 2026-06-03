from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from src.core.response import APIResponse
from src.domains.auth.auth_schema import ChangePasswordRequest, ForgotPasswordRequest, GoogleAuthRequest, RefreshTokenRequest, ResendOTPRequest, ResetPasswordRequest, RoleEnum, UserRegister, UserLogin, TokenResponse, OTPVerify
from src.domains.auth.services.auth_service import change_user_password, login_mobile_user, logout_user, register_mobile_user, renew_access_token, request_password_reset, resend_otp_code, reset_password_with_otp, verify_otp_and_login
from src.core.security import verify_password, create_access_token
from src.core.mongo import collections
from src.dependencies.dependencies import get_current_user
from src.domains.auth.services.oauth_service import login_with_google

# បង្កើត Router សម្រាប់ Mobile Auth
router = APIRouter(prefix="/api/auth", tags=["Mobile Authentication"])

@router.get("/roles", summary="ទាញយកបញ្ជី Role សម្រាប់ការចុះឈ្មោះ")
async def get_available_roles():
    """
    Route នេះប្រើសម្រាប់ឱ្យ Mobile App ទាញយកជម្រើស Role ដើម្បីបង្ហាញក្នុង Dropdown ។
    """
    # ទាញយកតម្លៃទាំងអស់ពី RoleEnum
    roles = [role.value for role in RoleEnum]
    
    return {
        "success": True,
        "message": "Roles fetched successfully",
        "data": roles
    }

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    ទទួលទិន្នន័យពី Mobile App ឆ្លងកាត់ការ Validate របស់ UserRegister 
    រួចបញ្ជូនទៅឱ្យ Service ជាអ្នកធ្វើការបញ្ចូលទៅ Database។
    """
    new_user = await register_mobile_user(user_data)
    return APIResponse(
        success=True,
        message="User registered successfully", 
        data=new_user
    )
    
@router.post("/login", response_model=APIResponse[TokenResponse], summary="ចូលគណនី (Login)")
async def login(login_data: UserLogin):
    """
    Route សម្រាប់ឱ្យអ្នកប្រើប្រាស់ចូលគណនី ដោយប្រើ Email និង Password។
    លទ្ធផលនឹងបញ្ចេញ Access Token, Refresh Token និងប្រវត្តិរូបសង្ខេប។
    """
    result = await login_mobile_user(login_data)
    
    return APIResponse(
        success=True,
        message="Login successful",
        data=result
    )
    
@router.post("/verify-otp", response_model=APIResponse[TokenResponse])
async def verify_otp(otp_data: OTPVerify):
    """
    Route នេះទទួលយក Email និង OTP ៦ ខ្ទង់ពី Mobile App
    បើផ្ទៀងផ្ទាត់ជោគជ័យ វានឹងបញ្ចេញ Token និងប្រវត្តិរូប (Auto-login) ត្រឡប់ទៅវិញតែម្តង
    """
    result = await verify_otp_and_login(otp_data)
    
    return APIResponse(
        success=True,
        message="OTP verification successful",
        data=result
    )

@router.post("/resend-otp", summary="សុំផ្ញើលេខកូដ OTP ម្តងទៀត")
async def resend_otp(request_data: ResendOTPRequest):
    """
    Route នេះប្រើសម្រាប់ផ្ញើ OTP ម្តងទៀត។ 
    (មានការពារ ៣០ វិនាទី ទើបអាចសុំម្តងទៀតបាន)
    """
    # ហៅ Service មកធ្វើការ
    await resend_otp_code(request_data)
    
    # បោះ Response តែមួយស្តង់ដារត្រឡប់ទៅ App
    return APIResponse[None](
        success=True,
        message="New OTP code has been sent to your email.",
        data=None
    )
    
@router.post("/forgot-password", summary="ភ្លេចពាក្យសម្ងាត់ (ស្នើសុំកូដ OTP)")
async def forgot_password(request_data: ForgotPasswordRequest):
    """
    Route សម្រាប់ឱ្យអ្នកប្រើប្រាស់វាយអ៊ីមែល ដើម្បីទទួលបានកូដ OTP ៦ ខ្ទង់។
    """
    await request_password_reset(request_data)
    return APIResponse[None](
        success=True,
        message="OTP code has been sent to your email.",
        data=None
    )

@router.post("/reset-password", summary="កំណត់ពាក្យសម្ងាត់ថ្មី (ដោយប្រើ OTP)")
async def reset_password(request_data: ResetPasswordRequest):
    """
    Route សម្រាប់ផ្ទៀងផ្ទាត់ OTP និងកំណត់ពាក្យសម្ងាត់ថ្មីក្នុងពេលតែមួយ។
    """
    await reset_password_with_otp(request_data)
    return APIResponse[None](
        success=True,
        message="Password has been reset successfully. Please log in with your new password.",
        data=None
    )
    
@router.post("/change-password", summary="ផ្លាស់ប្តូរពាក្យសម្ងាត់ (ទាមទារសិទ្ធិ/Token)")
async def change_password(
    request_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user) # 🎯 នេះជាអ្នកយាមទ្វារ (Guard)
):
    """
    Route នេះអាចហៅបាន លុះត្រាតែមានភ្ជាប់ Bearer Token នៅលើ Header។
    """
    # ទាញយក ID របស់ User ដែលកំពុង Login ទៅឱ្យ Service
    await change_user_password(user_id=current_user["id"], password_data=request_data)

    return APIResponse[None](
        success=True,
        message="Password has been changed successfully. Please log in with your new password.",
        data=None
    )
    
@router.post("/google-login", summary="Login ឬ Sign Up តាមរយៈ Google")
async def google_login(request_data: GoogleAuthRequest):
    """
    Route នេះប្រើសម្រាប់ទាំង Login និង Sign Up។ 
    តម្រូវឱ្យ Mobile App បញ្ជូន `id_token` របស់ Google មក។
    """
    result = await login_with_google(request_data)
    
    return APIResponse(
        success=True,
        message="ចូលគណនីតាមរយៈ Google បានជោគជ័យ",
        data=result
    )


@router.post("/refresh", summary="ប្តូរយក Access Token ថ្មី (ដោយប្រើ Refresh Token)")
async def refresh_token(request_data: RefreshTokenRequest):
    """
    Route នេះប្រើនៅពេល Access Token (៣០ នាទី) ផុតកំណត់។
    Mobile App ត្រូវបាញ់ Refresh Token មកទីនេះ ដើម្បីសុំ Access Token ថ្មី។
    """
    result = await renew_access_token(request_data)
    
    return APIResponse(
        success=True,
        message="New access token obtained successfully",
        data=result
    )
    
@router.post("/logout", summary="ចាកចេញពីគណនី (Logout)")
async def logout(
    request_data: RefreshTokenRequest,
    current_user: dict = Depends(get_current_user) # 🎯 តម្រូវឱ្យមាន Bearer Token 
):
    """
    Route នេះទាមទារឱ្យមាន Access Token ជាមុនសិន។
    បន្ទាប់មកវាទទួលយក Refresh Token ដើម្បីយកទៅបិទការប្រើប្រាស់នៅថ្ងៃក្រោយ។
    """
    # បញ្ជូនទាំង Token និង ID របស់ម្ចាស់គណនីទៅកាន់ Service
    await logout_user(request_data, str(current_user["_id"]))

    return APIResponse[None](
        success=True,
        message="You have been logged out successfully.",
        data=None
    )
    