from datetime import datetime, timezone
import os
from unicodedata import name
from aiosmtplib import email
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from src.core.mongo import collections
from src.domains.auth.auth_schema import GoogleAuthRequest
from src.core.security import create_access_token, create_refresh_token
from src.domains.auth.models.auth_model import create_user_model
from src.domains.auth.models.refresh_token_model import create_refresh_token_model
from dotenv import load_dotenv
import os

load_dotenv()

# ហៅ Collection មកប្រើ
users_collection = collections("users")
refresh_tokens_collection = collections("refresh_tokens")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

async def login_with_google(request_data: GoogleAuthRequest) -> dict:
    """
    មុខងារនេះទទួលបន្ទុកផ្ទៀងផ្ទាត់ Google Token និងធ្វើការ Merging / Auto-Register
    """
    # 1. ផ្ទៀងផ្ទាត់ Token ជាមួយ Google Server
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

    # 2. ស្វែងរកគណនីក្នុង Database 
    user = await users_collection.find_one({"email": email})

    if user:
        # លក្ខខណ្ឌ Account Merging
        if not user.get("is_active"):
            raise HTTPException(status_code=403, detail="This account is deactivated. Please contact support.")
            
        user_id = user["_id"]
        role = user["role"]
        
        # បើគាត់អត់ទាន់មានរូបថត យើងអាច Update រូបថតពី Google ឱ្យគាត់បាន
        if not user.get("avatar_url") and avatar_url:
            await users_collection.update_one({"_id": user_id}, {"$set": {"avatar_url": avatar_url}})
            
    else:
        # ករណី Sign Up Auto
        new_user = create_user_model(
            name=name,
            email=email,
            role=request_data.role.value, # ប្រើ .value ដើម្បីទាញយកពាក្យ "employee" ចេញពី Enum
            avatar_url=avatar_url,
            auth_provider="google",
            verified_at=datetime.now(timezone.utc) # Google គឺទុកចិត្តបាន អញ្ចឹង Verify ឱ្យតែម្តង
        )
        
        result = await users_collection.insert_one(new_user)
        user_id = result.inserted_id
        role = request_data.role
        user = new_user

    # 3. កត់ត្រាម៉ោង Login
    await users_collection.update_one(
        {"_id": user_id}, 
        {"$set": {"last_login_at": datetime.now(timezone.utc)}}
    )

    # 4. ផលិត Token
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