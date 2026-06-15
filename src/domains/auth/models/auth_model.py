from datetime import datetime, timezone
from bson import ObjectId

def create_user_model(
    first_name: str,
    last_name: str,
    email: str, 
    role: str, 
    password_hash: str = "", # ដាក់ "" ជា Default ព្រោះ Google អត់ត្រូវការ Password ទេ
    avatar_url: str = None,
    auth_provider: str = "local", 
    verified_at: datetime = None
) -> dict:
    
    return {
        "_id": ObjectId(),
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "avatar_url": avatar_url,
        "auth_provider": auth_provider,
        "is_active": True,
        "is_profile_completed": False,
        "verified_at": verified_at,
        "failed_login_attempts": 0, 
        "locked_until": None,
        "last_login_at": None,
        "deleted_at": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }