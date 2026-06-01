from datetime import datetime, timezone
from fastapi import HTTPException

from src.core.mongo import collections
from src.core.config import settings
from src.core.security import create_access_token, create_refresh_token
from src.core.security import create_access_token
from src.domains.auth.auth_helper import validate_password_and_lockout
from src.domains.auth.auth_helper import validate_password_and_lockout
from src.domains.auth.auth_schema import UserLogin
from src.domains.auth.models.refresh_token_model import create_refresh_token_model
from src.domains.auth.services.otp_service import generate_and_send_otp, verify_otp_code

users_collection = collections("users")
refresh_tokens_collection = collections("refresh_tokens")
async def login_admin_user(login_data: UserLogin) -> dict:
    user = await users_collection.find_one({"email": login_data.email})
    
    if not user:
        raise HTTPException(status_code=401, detail="អ៊ីមែល ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវទេ")

    if user.get("auth_provider") == "google":
        raise HTTPException(status_code=400, detail="គណនីនេះមិនអាចប្រើសម្រាប់សិទ្ធិ Admin បានទេ។")
        
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="អ្នកមិនមានសិទ្ធិចូលប្រើប្រាស់ផ្ទាំងនេះទេ។")

    await validate_password_and_lockout(user=user, password=login_data.password)
        
    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="គណនី Admin របស់អ្នកត្រូវបានផ្អាកដំណើរការ")

    # 🎯 លក្ខខណ្ឌ Bypass OTP
    if settings.REQUIRE_ADMIN_OTP:
        # បើទាមទារ OTP គឺគ្រាន់តែបាញ់ Email រួចប្រាប់ Frontend ឱ្យលោតផ្ទាំងវាយ OTP
        await generate_and_send_otp(user_id=user["_id"], email=user["email"], purpose="admin_login")
        return {
            "requires_otp": True,
            "email": user["email"],
            "message": "សូមពិនិត្យមើលអ៊ីមែលរបស់អ្នកសម្រាប់លេខកូដ OTP ៦ ខ្ទង់"
        }
    else:
        # បើ Bypass (False) គឺបញ្ចេញ Token ឱ្យតែម្តង!
        return await _generate_tokens_for_admin(user)

# ==========================================
# ជំហានទី ២: ផ្ទៀងផ្ទាត់ OTP និងបញ្ចេញ Token
# ==========================================
async def verify_admin_login_otp(email: str, otp_code: str) -> dict:
    user = await users_collection.find_one({"email": email})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=404, detail="រកមិនឃើញគណនី Admin នេះទេ")

    # ផ្ទៀងផ្ទាត់កូដ (វានឹង Throw Error បើកូដខុស ឬផុតកំណត់)
    await verify_otp_code(email=email, otp_code=otp_code, purpose="admin_login")
    
    # បើកូដត្រូវ បញ្ចេញ Token
    return await _generate_tokens_for_admin(user)

# ==========================================
# មុខងារជំនួយ (Helper) សម្រាប់ផលិត Token កុំឱ្យសរសេរកូដជាន់គ្នា
# ==========================================
async def _generate_tokens_for_admin(user: dict) -> dict:
    access_token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    refresh_token = create_refresh_token({"sub": str(user["_id"])})
    
    token_model = create_refresh_token_model(user_id=user["_id"], token=refresh_token)
    await refresh_tokens_collection.insert_one(token_model)
    
    # Update ម៉ោង Login
    await users_collection.update_one(
        {"_id": user["_id"]}, {"$set": {"last_login_at": datetime.now(timezone.utc)}}
    )
    
    return {
        "requires_otp": False, # ប្រាប់ Frontend ថា Login ចប់សព្វគ្រប់ហើយ
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "avatar_url": user.get("avatar_url")
        }
    }