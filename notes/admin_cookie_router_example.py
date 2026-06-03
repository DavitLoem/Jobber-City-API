"""
ឯកសារយោង: ការប្រើប្រាស់ HTTPOnly Cookie សម្រាប់ Web Security (XSS Protection)
ពេលចង់ Upgrade មកប្រើវិធីនេះ សូមកែប្រែ Router ឱ្យទៅជាទម្រង់ខាងក្រោម។
"""

from fastapi import APIRouter, Depends, Response, Request
from src.core.response import APIResponse
from src.dependencies.dependencies import get_current_user
from src.domains.auth.auth_schema import UserLogin
from src.domains.auth.services.admin_auth_service import login_admin_user

router = APIRouter(prefix="/api/v1/admin/cookie-auth", tags=["Admin Cookie Auth"])

# ==========================================
# 1. ការបញ្ចេញ Cookie ពេល Login
# ==========================================
@router.post("/login")
async def admin_login_with_cookie(login_data: UserLogin, response: Response):
    # 1. ដំណើរការ Login ធម្មតា
    result = await login_admin_user(login_data)
    
    # 2. 🎯 ទាញយក Refresh Token មកញាត់ចូល Cookie
    # max_age = 7 ថ្ងៃ (គិតជាវិនាទី) 
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,  # កូដ JS ក្នុង Frontend មិនអាចអានបានទេ (ការពារ XSS 100%)
        secure=True,    # ត្រូវតែប្រើ HTTPS (ដាក់ False សិនបើ Test ក្នុង Localhost)
        samesite="lax", # អនុញ្ញាតឱ្យ Browser ភ្ជាប់វាទៅ API (បើទិញ Domain តែមួយ)
        max_age=7 * 24 * 60 * 60 
    )
    
    # 3. លុប Refresh Token ចេញពី JSON ព្រោះយើងបានលាក់វាក្នុង Cookie រួចហើយ
    del result["refresh_token"]
    
    return APIResponse(success=True, message="Login ជោគជ័យ", data=result)


# ==========================================
# 2. ការអាន និងការលុប Cookie ពេល Logout
# ==========================================
@router.post("/logout")
async def admin_logout_with_cookie(
    request: Request, 
    response: Response, 
    current_user: dict = Depends(get_current_user)
):
    # 1. 🎯 ចាប់យក Token ពីក្នុង Cookie មកវិញ (Frontend មិនបាច់បញ្ជូនមកទេ)
    refresh_token = request.cookies.get("refresh_token")
    
    # 2. បើមាន Token, យកវាទៅបិទសិទ្ធិ (Revoke) ក្នុង Database 
    # (តម្រូវឱ្យមាន Function មួយដែលទទួលយកអក្សរ Token សុទ្ធ)
    if refresh_token:
        # await revoke_token_in_db(refresh_token) # ឧទាហរណ៍ Function ក្នុង Service
        pass 

    # 3. 🎯 លុប Cookie នោះចោលពី Browser របស់អ្នកប្រើប្រាស់
    response.delete_cookie("refresh_token")
    
    return APIResponse(success=True, message="Logout ជោគជ័យ", data=None)