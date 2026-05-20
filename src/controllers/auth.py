import datetime
import os
import jwt
from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form
from typing import Optional
from src.config.mongo import collections
from src.model.auth import CreateAccount, LoginAccount, PinCodeVerify, ResetPassword, Forgotpassword
from src.services.auth import find_user_by_id, insert_new_acc, get_password_hash, login_service, find_and_verify_by_pin, create_otp, get_all_job_types
from src.config.cloudinary import upload_image, delete_image

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.get("/job-types", summary="Get options for Choose Your Job Type")
async def get_job_types():
    return {
        "status": "success",
        "data": get_all_job_types()
    }

@router.post("/create_account", summary="Create a new Account")
async def create_account(body: CreateAccount = Body(...)):
    # ១. បញ្ចូលទិន្នន័យទៅក្នុង Database តាមរយៈ service
    result = insert_new_acc(body.email, body.password, body.job_type_id)
    
    # ២. បើមានកំហុស (ដូចជា Email ជាន់គ្នា) ឱ្យលោត Error ទៅ Frontend
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("message"))

    # ៣. (Optional) ទាញទិន្នន័យ User ដែលទើបបង្កើតរួចមកបង្ហាញ
    # ចំណាំ៖ ក្នុង insert_new_acc ត្រូវ return "user_id" មកជាមួយទើបប្រើត្រង់នេះបាន
    user = find_user_by_id(result.get("user_id"))
    
    return {
        "status": "success",
        "message": "User Created Account successfully",
        "data": user 
    }


@router.post("/login", summary="Login a user")
async def user_login(body: LoginAccount = Body(...)):
    # ១. ហៅ Service ដើម្បីផ្ទៀងផ្ទាត់ Email និង Password
    user = login_service(body.email, body.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # ២. រៀបចំ Payload សម្រាប់ JWT
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "user_id": str(user["_id"]),
        "iat": now, # កាលបរិច្ឆេទបង្កើត
        "exp": now + datetime.timedelta(hours=24) # ផុតកំណត់ក្នុង ២៤ ម៉ោង
    } 

    # ៣. បង្កើត Token (កែ algorithm ឱ្យត្រូវ syntax)
    secret_key = os.getenv("SECRET_KEY", "your_super_secret_key")
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    # ៤. បញ្ជូនទិន្នន័យទៅវិញ
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]), 
            "email": user["email"]
        }
    }


@router.post("/forgot-password", summary="Request PIN for forgot password")
async def request_forgot_password(body: Forgotpassword = Body(...)):
    # ១. ហៅ Service ដើម្បីបង្កើត OTP និងផ្ញើទៅកាន់ User
    # Service នេះគួរតែឆែកថា តើត្រូវផ្ញើតាម Email ឬ Phone
    result = create_otp(email=body.email, phone=body.phone)
    
    # ២. ឆែកមើលថា តើមាន User ហ្នឹងក្នុង DB ឬអត់
    if not result.get("user_found"):
        raise HTTPException(status_code=404, detail="User not found with this identity")

    # ៣. ឆែកមើលការផ្ញើ (តើផ្ញើជោគជ័យតាមច្រកណាមួយឬទេ?)
    if not result.get("success"):
        raise HTTPException(
            status_code=500, 
            detail=result.get("message", "Failed to send verification code")
        )
        
    return {
        "status": "success",
        "message": f"PIN code sent successfully to your {result.get('sent_via')}"
    }

# --- STEP 2: VERIFY PIN ---
@router.post("/verify-pin")
async def verify_pin_code(body: PinCodeVerify = Body(...)):
    result = find_and_verify_by_pin(
        email=body.email,
        pin_code=body.pin_code
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {
        "status": "success",
        "message": "PIN verified successfully",
        "email": result.get("email")
    }

# --- STEP 3: RESET PASSWORD ---
@router.post("/reset-password")
async def reset_password(body: ResetPassword = Body(...)):
    # ១. ការផ្ទៀងផ្ទាត់ Password ត្រូវបានធ្វើរួចរាល់ដោយ Pydantic Validator ដែលយើងបានសរសេរមុននេះ
    
    # ២. Hash password ថ្មី
    hashed = get_password_hash(body.new_password)
    
    # ៣. Update ក្នុង DB (ក្នុងករណីប្រើ Email ឬ Phone)
    query = {}
    if body.email:
        query = {"email": body.email}
    elif body.phone:
        query = {"phone": body.phone}

    collections_to_check = ["users", "employee", "employer"]
    updated = False
    
    for collection_name in collections_to_check:
        user_col = collections(collection_name)
        result = user_col.update_one(
            query,
            {"$set": {"password": hashed}}
        )
        
        if result.modified_count > 0:
            updated = True
            break
    
    if not updated:
        raise HTTPException(status_code=400, detail="User not found or password already reset")
    
    return {"message": "Password reset successfully"}

