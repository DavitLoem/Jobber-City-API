from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from src.core.security import verify_token
from src.core.mongo import collections
from bson import ObjectId
from typing import List

# 1. ត្រឡប់មកប្រើ HTTPBearer វិញ
security = HTTPBearer()

# 2. ប្រើ credentials វិញ
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    យក Access Token ពី Header មក Decode រួចស្វែងរក User ក្នុង Database
    """
    # វានឹងទាញយក Access Token ដែលអ្នក Paste ក្នុងប៊ូតុងសោរ (ឬផ្ញើពី Postman)
    token = credentials.credentials 
    payload = verify_token(token) 
    
    user_id = payload.get("sub") 
    if not user_id:
        raise HTTPException(status_code=401, detail="Token មិនមានផ្ទុក User ID ទេ")

    users_collection = collections("users")
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="រកមិនឃើញគណនីអ្នកប្រើប្រាស់")
    
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        """កំណត់ទុកជាមុននូវ Role ណាខ្លះដែលអាចឆ្លងកាត់បាន"""
        self.allowed_roles = allowed_roles

    def __call__(self, user: dict = Depends(get_current_user)):
        """
        Function នេះនឹងដំណើរការដោយស្វ័យប្រវត្តិពេល Router ហៅវា។
        វាពឹងផ្អែកលើ get_current_user ដើម្បីទាញយក User មកសិន ទើបឆែក Role តាមក្រោយ។
        """
        user_role = user.get("role")
        
        # ប្រសិនបើគណនីគ្មាន Role ឬ Role មិនស្ថិតក្នុងបញ្ជីដែលអនុញ្ញាតទេ គឺទាត់ចោល (403 Forbidden)
        if not user_role or user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=403, 
                detail="Permission Denied! អ្នកមិនមានសិទ្ធិក្នុងការប្រើប្រាស់មុខងារនេះទេ។"
            )
        
        return user # បើមានសិទ្ធិ បញ្ជូនទិន្នន័យ User នោះទៅឱ្យ Router បន្ត
    
require_admin = RoleChecker(["admin"])
require_employer = RoleChecker(["employer"])
require_employee = RoleChecker(["employee"])
require_mobile_users = RoleChecker(["employer", "employee"])