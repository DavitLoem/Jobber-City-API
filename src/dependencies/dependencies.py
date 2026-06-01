from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from src.core.security import verify_token
from src.core.mongo import collections
from bson import ObjectId

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