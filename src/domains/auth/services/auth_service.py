from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException, status
from src.core.mongo import collections
from src.core.security import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from src.domains.auth.auth_helper import validate_password_and_lockout
from src.domains.auth.auth_schema import ChangePasswordRequest, ForgotPasswordRequest, OTPVerify, ResendOTPRequest, RefreshTokenRequest, ResetPasswordRequest, UserLogin, UserRegister
from src.domains.auth.models.auth_model import create_user_model
from src.domains.auth.models.refresh_token_model import create_refresh_token_model
from src.domains.auth.services.otp_service import generate_and_send_otp, verify_otp_code

# Collection
users_collection = collections("users")
otps_collection = collections("otps")
refresh_tokens_collection = collections("refresh_tokens")

async def register_mobile_user(user_data: UserRegister) -> dict:
    # ឆែកមើលអ៊ីមែល
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already in use.")

    # បង្កើត User ចូល Database
    hashed_pwd = hash_password(user_data.password)
    new_user_dict = create_user_model(
        name=user_data.name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        password_hash=hashed_pwd,
        role=user_data.role.value
    )
    result = await users_collection.insert_one(new_user_dict)
    
    # 🎯 ហៅមុខងារ OTP (កូដ ៣ បន្ទាត់ជំនួសកូដវែងៗពីមុន)
    await generate_and_send_otp(user_id=result.inserted_id, email=user_data.email)

    new_user_dict["id"] = str(result.inserted_id)
    del new_user_dict["_id"]
    del new_user_dict["password_hash"]
    return new_user_dict

async def login_mobile_user(login_data: UserLogin) -> dict:
    # 1. ស្វែងរក User តាម Email
    user = await users_collection.find_one({"email": login_data.email})
    
    # 2. ឆែកមើលថាមាន User នេះ ឬ Password ត្រូវគ្នាដែរឬទេ?
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password."
        )
        
    # 🎯 បន្ថែមការការពារទី ១: ឆែកមើលក្រែងគាត់ចុះឈ្មោះតាម Google
    if user.get("auth_provider") == "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is registered via Google. Please log in with Google."
        )
        
    await validate_password_and_lockout(user=user, password=login_data.password)

    # 3. ឆែកមើលថាតើគាត់បាន Verify OTP ហើយឬនៅ?
    if not user.get("verified_at"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Please verify your account (OTP) before logging in."
        )
        
    # 4. ឆែកមើលក្រែងលោគណនីនេះត្រូវ Admin បិទ (Banned/Disabled)
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Your account is disabled."
        )

    # 5. [ស្រេចចិត្ត] កត់ត្រាម៉ោងដែលគាត់ Login ចុងក្រោយ (Update last_login_at)
    await users_collection.update_one(
        {"_id": user["_id"]}, 
        {"$set": {"last_login_at": datetime.now(timezone.utc)}}
    )

    # 6. ផលិត Token ទាំងពីរ (Access & Refresh)
    access_token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    refresh_token = create_refresh_token({"sub": str(user["_id"])})
    
    # Save Refresh Token ចូល DB
    token_model = create_refresh_token_model(user_id=user["_id"], token=refresh_token)
    await refresh_tokens_collection.insert_one(token_model)
    
    # 7. បោះទិន្នន័យត្រឡប់ទៅវិញ (ទម្រង់ដូចគ្នា នឹងមុខងារ Verify OTP បេះបិទ)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "is_profile_completed": user.get("is_profile_completed", False),
            "avatar_url": user.get("avatar_url")
        }
    }

async def verify_otp_and_login(otp_data: OTPVerify) -> dict:
    # 🎯 ហៅមុខងារផ្ទៀងផ្ទាត់ OTP
    valid_otp = await verify_otp_code(email=otp_data.email, otp_code=otp_data.otp_code)

    # Update User ថា Verified រួច
    user = await users_collection.find_one_and_update(
        {"_id": valid_otp["user_id"]},
        {"$set": {"verified_at": datetime.now(timezone.utc)}},
        return_document=True 
    )

    # ផលិតសោរទាំងពីរ
    access_token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    refresh_token = create_refresh_token({"sub": str(user["_id"])})
    
    # Save Refresh Token
    token_model = create_refresh_token_model(user_id=user["_id"], token=refresh_token)
    await refresh_tokens_collection.insert_one(token_model)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "is_profile_completed": user["is_profile_completed"]
        }
    }

async def resend_otp_code(request_data: ResendOTPRequest) -> bool:
    # 1. ឆែកមើលគណនី
    user = await users_collection.find_one({"email": request_data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email."
        )
        
    if user.get("verified_at"):
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account has already been verified."
        )

    # 2. 🎯 ឆែកសុវត្ថិភាព ៣០ វិនាទី (Rate Limiting)
    # ទាញយក OTP ចុងក្រោយបង្អស់របស់គាត់មកឆែកម៉ោង
    cursor = otps_collection.find({"email": request_data.email, "purpose": "register"}).sort("created_at", -1).limit(1)
    otps = await cursor.to_list(length=1)

    if otps:
        latest_otp = otps[0]
        # គណនាចន្លោះពេលពីការសុំលើកមុន ដល់ម៉ោងឥឡូវ
        time_diff = datetime.now(timezone.utc) - latest_otp["created_at"].replace(tzinfo=timezone.utc)
        seconds_passed = time_diff.total_seconds()

        if seconds_passed < 30:
            wait_time = 30 - int(seconds_passed)
            # ប្រើ 429 Too Many Requests គឺជាស្តង់ដារអន្តរជាតិសម្រាប់ការ Request ញឹកញាប់ពេក
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
                detail=f"Please wait {wait_time} minutes before requesting a new code."
            )

    # 3. បើហួស ៣០ វិនាទីហើយ អនុញ្ញាតឱ្យផ្ញើកូដថ្មី
    await generate_and_send_otp(user_id=user["_id"], email=request_data.email)
    
    return True

async def request_password_reset(request_data: ForgotPasswordRequest) -> bool:
    user = await users_collection.find_one({"email": request_data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No account found with this email."
        )
        
    if user.get("auth_provider") == "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is registered via Google. Please log in with Google."
        )
    
    # ប្រើ purpose="reset_password" ដើម្បីកុំឱ្យច្រឡំជាមួយ OTP ពេល Register
    await generate_and_send_otp(user_id=user["_id"], email=request_data.email, purpose="reset_password")
    return True

async def reset_password_with_otp(request_data: ResetPasswordRequest) -> bool:
    # 1. ស្វែងរកគណនី
    user = await users_collection.find_one({"email": request_data.email})
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email.")
    
    if user.get("auth_provider") == "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is registered via Google. Please log in with Google."
        )

    # 2. 🎯 ផ្ទៀងផ្ទាត់ OTP (ប្រើ purpose="reset_password") 
    # មុខងារនេះនឹងឆែកម៉ោងផុតកំណត់ និងដុតកម្ទេច OTP នោះចោលដោយស្វ័យប្រវត្តិ
    await verify_otp_code(email=request_data.email, otp_code=request_data.otp_code, purpose="reset_password")

    # 3. Hash ពាក្យសម្ងាត់ថ្មី
    new_hashed_password = hash_password(request_data.new_password)

    # 4. Update ពាក្យសម្ងាត់ចូល Database និងដោះសោរ Block គណនី (បើសិនជាគាត់ធ្លាប់ជាប់ Lock)
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "password_hash": new_hashed_password,
            "failed_login_attempts": 0,
            "locked_until": None,
            "updated_at": datetime.now(timezone.utc)
        }}
    )

    # 5. [សុវត្ថិភាព] ដកហូតសិទ្ធិ Token ចាស់ៗទាំងអស់ ដើម្បីឱ្យទូរស័ព្ទផ្សេងទៀត Logout ដោយស្វ័យប្រវត្តិ
    await refresh_tokens_collection.update_many(
        {"user_id": user["_id"]},
        {"$set": {"is_revoked": True}}
    )

    return True

async def change_user_password(user_id: str, password_data: ChangePasswordRequest) -> bool:
    """
    មុខងារនេះអាចយកទៅប្រើបានគ្រប់ Role ទាំងអស់ (Mobile, Admin...)។
    វាទាមទារឱ្យ User មានសិទ្ធិ Login រួចរាល់ទើបអាចដំណើរការបាន។
    """
    # 1. ស្វែងរកគណនីក្នុង Database
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # 2. ផ្ទៀងផ្ទាត់ពាក្យសម្ងាត់ចាស់
    if not verify_password(password_data.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    # 3. បង្កើតកូដសម្ងាត់ថ្មី (Hash)
    new_hashed_password = hash_password(password_data.new_password)

    # 4. Update ចូល Database
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password_hash": new_hashed_password, "updated_at": datetime.now(timezone.utc)}}
    )

    # 5. [សុវត្ថិភាពបន្ថែម] លុប Refresh Token ចាស់ៗចោល ដើម្បីឱ្យ Device ផ្សេងៗ Logout
    await refresh_tokens_collection.update_many(
        {"user_id": ObjectId(user_id)},
        {"$set": {"is_revoked": True}}
    )

    return True
    
async def renew_access_token(data: RefreshTokenRequest) -> dict:
    # 1. ឆែកមើលថាតើ Token នេះពិតជារបស់យើង និងមិនទាន់ផុតកំណត់ ៧ ថ្ងៃមែនទេ?
    payload = verify_token(data.refresh_token)
    user_id = payload.get("sub")

    # 2. ឆែកក្នុង Database ក្រែងលោវាត្រូវ Admin បិទចោល (Revoked) 
    saved_token = await refresh_tokens_collection.find_one({
        "token": data.refresh_token,
        "user_id": ObjectId(user_id)
    })

    if not saved_token or saved_token["is_revoked"]:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token.")

    # 3. ទាញយក User ដើម្បីយក Role មកញាត់ចូល Token ថ្មី
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="Your account is disabled.")

    # 4. ផលិត Access Token ថ្មី (៣០ នាទី) ជូនគាត់វិញ
    new_access_token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})

    # ចំណាំ: យើងមិនបាច់បោះ User Profile ទៅវិញទេ ព្រោះ App មានរួចហើយ។ គេត្រូវការតែ Token ថ្មី។
    return {
        "access_token": new_access_token,
        "refresh_token": data.refresh_token, # បោះរបស់ចាស់ឱ្យគាត់កាន់ដដែល
        "token_type": "bearer"
    }
    
async def logout_user(request_data: RefreshTokenRequest, user_id: str) -> bool:
    """
    បិទ (Revoke) Refresh Token ដោយផ្ទៀងផ្ទាត់ថាវាពិតជារបស់ User នេះមែន។
    """
    await refresh_tokens_collection.update_one(
        {
            "token": request_data.refresh_token, 
            "user_id": ObjectId(user_id) # 🎯 ត្រូវប្រាកដថា Token នេះជារបស់គាត់មែន
        },
        {"$set": {"is_revoked": True}}
    )
    return True