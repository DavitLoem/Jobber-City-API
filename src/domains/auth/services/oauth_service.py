from datetime import datetime, timezone
import os
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from src.core.mongo import collections
from src.domains.auth.auth_schema import GoogleAuthRequest
from src.domains.auth.models.auth_model import create_user_model
from dotenv import load_dotenv

# 🎯 Import អនុគមន៍ពី auth_service មកប្រើ ដើម្បីឱ្យ Response ចេញមកដូចគ្នាបេះបិទ
from src.domains.auth.services.auth_service import _generate_login_response

load_dotenv()

users_collection = collections("users")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") 

async def login_with_google(request_data: GoogleAuthRequest) -> dict:
    try:
        idinfo = id_token.verify_oauth2_token(
            request_data.id_token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        email = idinfo['email']
        
        # ទាញយក first_name និង last_name ពី Google ដើម្បីឱ្យត្រូវជាមួយ Schema ថ្មី
        first_name = idinfo.get('given_name', 'Google')
        last_name = idinfo.get('family_name', 'User')
        avatar_url = idinfo.get('picture', None)
        
    except ValueError:
        raise HTTPException(status_code=401, detail="Google Token Invalid")

    user = await users_collection.find_one({"email": email})

    if user:
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Account is deactivated.")
            
        existing_role = user.get("role")
        
        # 🎯 ជំហានទី ១៖ បើមានបោះ role មក (មកពីទំព័រ Register) ទើបយើងឆែក Role Mismatch
        if request_data.role:
            requested_role = request_data.role.value
            
            if existing_role != requested_role:
                # បោះ Error 409 ជាមួយនឹង JSON detail ដើម្បីឱ្យ Flutter ងាយស្រួលចាប់យកទៅប្រើ
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error_code": "ROLE_MISMATCH",
                        "existing_role": existing_role,
                        "message": f"This email is already registered as a {existing_role}."
                    }
                )
        
        # បើអត់មានបោះ role ទេ (មកពីទំព័រ Login) ឬ បោះមកត្រូវ Role គ្នា គឺអនុញ្ញាតឱ្យចូល
        user_id = user["_id"]
        
        # Update រូបថតបើសិនជាអត់ទាន់មាន
        if not user.get("avatar_url") and avatar_url:
            await users_collection.update_one({"_id": user_id}, {"$set": {"avatar_url": avatar_url}})
            # Update ក្នុង variable ផ្ទាល់ ដើម្បីឱ្យ _generate_login_response យកទៅប្រើបានភ្លាមៗ
            user["avatar_url"] = avatar_url
            
    else:
        # 🎯 ជំហានទី ២៖ ករណីរកមិនឃើញគណនីក្នុងប្រព័ន្ធ (Email ថ្មី)
        if not request_data.role:
            # បើអត់បោះ role មក (មកពីទំព័រ Login) យើងបដិសេធ ព្រោះយើងមិនអាច Auto-Register ឱ្យបានទេ
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "ACCOUNT_NOT_FOUND",
                    "message": "We couldn't find an account associated with this Google email. Please register first."
                }
            )
            
        # បើមានបោះ role មក (មកពីទំព័រ Register) ធ្វើការបង្កើតគណនីថ្មី (Auto-register)
        new_user = create_user_model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=request_data.role.value, 
            avatar_url=avatar_url,
            auth_provider="google",
            verified_at=datetime.now(timezone.utc) 
        )
        
        result = await users_collection.insert_one(new_user)
        # បញ្ចូល _id ទៅក្នុង dictionary ដើម្បីកុំឱ្យ _generate_login_response លោត Error
        new_user["_id"] = result.inserted_id
        user = new_user

    # កត់ត្រាម៉ោង Login
    await users_collection.update_one(
        {"_id": user["_id"]}, 
        {"$set": {"last_login_at": datetime.now(timezone.utc)}}
    )

    # ប្រើប្រាស់អនុគមន៍រួម វានឹងរ៉ាប់រងការបង្កើត Token និងឆែក Onboarding ឱ្យដោយស្វ័យប្រវត្តិ
    return await _generate_login_response(user, is_normal_login=False)