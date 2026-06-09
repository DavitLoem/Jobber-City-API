import random
from datetime import datetime, timezone
from fastapi import HTTPException
from src.core.mongo import collections
from src.core.security import hash_password, verify_password
from src.domains.auth.models.otp_model import create_otp_model
from src.utils.email_sender import send_otp_email

otps_collection = collections("otps")

async def generate_and_send_otp(user_id, email: str, purpose: str = "register"):
    """មុខងារសម្រាប់បង្កើតលេខកូដ Save ចូល DB និងបាញ់អ៊ីមែល"""
    # 1. បង្កើតលេខកូដ Random ៦ ខ្ទង់
    otp_code_plain = str(random.randint(100000, 999999))
    otp_hash = hash_password(otp_code_plain)

    # 2. Save ចូល Database
    otp_dict = create_otp_model(user_id=user_id, email=email, otp_hash=otp_hash, purpose=purpose)
    await otps_collection.insert_one(otp_dict)

    # 3. បាញ់អ៊ីមែលទៅកាន់អ្នកប្រើប្រាស់
    await send_otp_email(email, otp_code_plain)
    return True

async def verify_otp_code(email: str, otp_code: str, purpose: str = "register") -> dict:
    """មុខងារសម្រាប់ផ្ទៀងផ្ទាត់លេខកូដដែល User វាយបញ្ចូល។ បើជោគជ័យ វានឹង Return ទិន្នន័យ OTP នោះ"""
    cursor = otps_collection.find({"email": email, "purpose": purpose}).sort("created_at", -1).limit(1)
    otps = await cursor.to_list(length=1)

    if not otps:
        raise HTTPException(status_code=400, detail="No OTP found for this email")
    
    latest_otp = otps[0]

    if latest_otp["is_used"]:
        raise HTTPException(status_code=400, detail="This OTP code has already been used")
    
    if latest_otp["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This OTP code has expired")

    if not verify_password(otp_code, latest_otp["otp_hash"]):
        raise HTTPException(status_code=400, detail="This OTP code is invalid")

    # បើត្រូវទាំងអស់ ដុតកម្ទេចវាចោល
    await otps_collection.update_one({"_id": latest_otp["_id"]}, {"$set": {"is_used": True}})
    
    return latest_otp

async def verify_otp_code(email: str, otp_code: str, purpose: str = "register") -> dict:
    """មុខងារសម្រាប់ផ្ទៀងផ្ទាត់លេខកូដដែល User វាយបញ្ចូល។"""
    
    # 🎯 ទី១: កាត់ចោលរាល់ការដកឃ្លា ឬ Space ដែលមើលមិនឃើញ
    clean_otp_code = str(otp_code).strip()
    
    cursor = otps_collection.find({"email": email, "purpose": purpose}).sort("created_at", -1).limit(1)
    otps = await cursor.to_list(length=1)

    if not otps:
        raise HTTPException(status_code=400, detail="No OTP found for this email")
    
    latest_otp = otps[0]

    if latest_otp["is_used"]:
        raise HTTPException(status_code=400, detail="This OTP code has already been used")
    
    if latest_otp["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This OTP code has expired")
    
    # ប្រើ clean_otp_code ដែលបានកាត់ Space រួច យកមកផ្ទៀងផ្ទាត់
    if not verify_password(clean_otp_code, latest_otp["otp_hash"]):
        print("Failed OTP verification attempt for email:", email) # Log សម្រាប់ Debug
        raise HTTPException(status_code=400, detail="This OTP code is invalid")

    # បើត្រូវទាំងអស់ ដុតកម្ទេចវាចោល
    await otps_collection.update_one({"_id": latest_otp["_id"]}, {"$set": {"is_used": True}})
    
    return latest_otp