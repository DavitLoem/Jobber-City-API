import datetime
import os
import jwt
from fastapi import APIRouter, HTTPException, Body
from src.model.auth import CreateAccount, LoginAccount, PinCodeVerify, ResetPassword, Forgotpassword
from src.services.auth import find_user_by_id, insert_new_acc, get_password_hash, login_service, find_and_verify_by_pin, create_otp, get_all_job_types

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.get("/job-types", summary="Get options for Choose Your Job Type")
async def get_job_types():
    return {
        "status": "success",
        "data": get_all_job_types()
    }

@router.post("/create_account", summary="Create a new Account")
async def create_account(body: CreateAccount = Body(...)):
    result = insert_new_acc(body.email, body.password, body.job_type_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("message"))

    user = find_user_by_id(result.get("user_id"))
    
    return {
        "status": "success",
        "message": "User Created Account successfully",
        "data": user 
    }

@router.post("/login", summary="Login a user")
async def user_login(body: LoginAccount = Body(...)):
    user = login_service(body.email, body.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "user_id": str(user["_id"]),
        "iat": now, 
        "exp": now + datetime.timedelta(hours=24) 
    } 

    secret_key = os.getenv("SECRET_KEY", "your_super_secret_key")
    token = jwt.encode(payload, secret_key, algorithm="HS256")

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
    # 🎯 ហៅមុខងារបង្កើត OTP ដោយបោះទៅតែ email មួយមុខគត់
    result = create_otp(email=body.email)
    
    if not result.get("user_found"):
        raise HTTPException(status_code=404, detail="User not found with this identity")

    if not result.get("success"):
        raise HTTPException(
            status_code=500, 
            detail=result.get("message", "Failed to send verification code")
        )
        
    return {
        "status": "success",
        "message": "PIN code sent successfully to your email"
    }

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

@router.post("/reset-password")
async def reset_password(body: ResetPassword = Body(...)):
    from src.config.mongo import collections
    hashed = get_password_hash(body.new_password)
    
    query = {"email": body.email}

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