from fastapi import APIRouter, Depends, HTTPException, status
from src.core.response import APIResponse
from src.domains.auth.auth_schema import RefreshTokenRequest, UserLogin, TokenResponse
from src.domains.auth.services.admin_auth_service import login_admin_user
from src.domains.auth.services.auth_service import logout_user
from src.dependencies.dependencies import get_current_user

router = APIRouter(prefix="/api/admin/auth", tags=["Admin Authentication"])

@router.post("/login", response_model=APIResponse[TokenResponse], summary="Admin ចូលគណនី (Login)")
async def admin_login(login_data: UserLogin):
    result = await login_admin_user(login_data)
    return APIResponse(success=True, message="ចូលគណនី Admin បានជោគជ័យ", data=result)

@router.post("/logout", summary="Admin ចាកចេញពីគណនី (Logout)")
async def admin_logout(
    request_data: RefreshTokenRequest, # 🎯 ទទួលយក Refresh Token ពី Frontend (ដូច Mobile ដែរ)
    current_user: dict = Depends(get_current_user)
):
    """
    Route សម្រាប់ Admin ចាកចេញពីគណនី និងបិទសិទ្ធិ Token ចាស់។
    """
    # ហៅ Service របស់ Mobile មកប្រើឡើងវិញបានយ៉ាងស្រួល
    await logout_user(request_data, str(current_user["_id"]))
    
    return APIResponse[None](
        success=True,
        message="ចាកចេញពីគណនី Admin បានជោគជ័យ",
        data=None
    )