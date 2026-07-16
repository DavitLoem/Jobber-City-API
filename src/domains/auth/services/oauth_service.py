from datetime import datetime, timezone
import os
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from src.core.mongo import collections
from src.domains.auth.auth_schema import GoogleAuthRequest
from src.core.security import create_access_token, create_refresh_token
from src.domains.auth.models.auth_model import create_user_model
from src.domains.auth.models.refresh_token_model import create_refresh_token_model
from dotenv import load_dotenv

load_dotenv()

users_collection = collections("users")
refresh_tokens_collection = collections("refresh_tokens")

# សំខាន់៖ នេះត្រូវតែជា "Web Client ID" មិនមែន Android Client ID ទេ
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") 

async def login_with_google(request_data: GoogleAuthRequest) -> dict:
    try:
        idinfo = id_token.verify_oauth2_token(
            request_data.id_token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        email = idinfo['email']
        name = idinfo.get('name', 'Google User')
        avatar_url = idinfo.get('picture', None)
        
    except ValueError:
        raise HTTPException(status_code=401, detail="Google Token Invalid")

    user = await users_collection.find_one({"email": email})

    if user:
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Account is deactivated.")
            
        user_id = user["_id"]
        role = user["role"]
        
        if not user.get("avatar_url") and avatar_url:
            await users_collection.update_one({"_id": user_id}, {"$set": {"avatar_url": avatar_url}})
    else:
        new_user = create_user_model(
            name=name,
            email=email,
            role=request_data.role.value, 
            avatar_url=avatar_url,
            auth_provider="google",
            verified_at=datetime.now(timezone.utc) 
        )
        
        result = await users_collection.insert_one(new_user)
        user_id = result.inserted_id
        # កែត្រង់នេះ៖ ទាញយកតម្លៃ String ចេញពី Enum
        role = request_data.role.value 
        user = new_user

    await users_collection.update_one(
        {"_id": user_id}, 
        {"$set": {"last_login_at": datetime.now(timezone.utc)}}
    )

    access_token = create_access_token({"sub": str(user_id), "role": role})
    refresh_token = create_refresh_token({"sub": str(user_id)})
    
    token_model = create_refresh_token_model(user_id=user_id, token=refresh_token)
    await refresh_tokens_collection.insert_one(token_model)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user_id),
            "name": user.get("name", name),
            "email": email,
            "role": role,
            "is_profile_completed": user.get("is_profile_completed", False),
            "avatar_url": user.get("avatar_url", avatar_url)
        }
    }