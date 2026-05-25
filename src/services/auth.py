from datetime import datetime, timedelta
from typing import Collection, Optional
import random
import smtplib
import os
from email.mime.text import MIMEText
from bson import ObjectId, errors
from src.config.mongo import collections 
from src.model.auth import JobType
from passlib.context import CryptContext

def get_all_job_types():
    """ទាញយកប្រភេទការងារទាំងអស់សម្រាប់បង្ហាញក្នុង UI"""
    return [
        {"id": "FIND_JOB", "title": JobType.FIND_JOB.value, "description": "I want to find a job for me."},
        {"id": "FIND_EMPLOYEE", "title": JobType.FIND_EMPLOYEE.value, "description": "I want to find employees."}
    ]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def cleanup_expired_otps():
    """Delete expired OTPs from database"""
    otp_col = collections("otp_codes")
    result = otp_col.delete_many({"expires_at": {"$lt": datetime.now()}})
    if result.deleted_count > 0:
        print(f"[INFO] Cleaned up {result.deleted_count} expired OTPs")

def check_email_exists_across_all_collections(email: str):
    collections_to_check = ["users", "employee", "employer"]
    
    for collection_name in collections_to_check:
        current_col = collections(collection_name)
        user = current_col.find_one({"email": email})
        if user:
            return {
                "exists": True,
                "collection": collection_name,
                "user_id": str(user["_id"])
            }
    
    return {"exists": False, "collection": None, "user_id": None}

# 🎯 បន្ថែមមកវិញ៖ មុខងារឆែក Email សម្រាប់ Update Profile (ដោះស្រាយកំហុស ImportError)
def check_email_uniqueness_for_update(email: str, exclude_user_id: str = None):
    collections_to_check = ["users", "employee", "employer"]
    
    for collection_name in collections_to_check:
        current_col = collections(collection_name)
        query = {"email": email}
        
        if exclude_user_id:
            try:
                query["_id"] = {"$ne": ObjectId(exclude_user_id)}
            except errors.InvalidId:
                pass
        
        user = current_col.find_one(query)
        if user:
            return {
                "exists": True,
                "collection": collection_name,
                "user_id": str(user["_id"])
            }
    
    return {"exists": False, "collection": None, "user_id": None}

def insert_new_acc(email: str, password: str, job_type_id: Optional[str] = None):
    email_check = check_email_exists_across_all_collections(email)
    if email_check["exists"]:
        collection_names = {
            "users": "basic user account",
            "employee": "employee account", 
            "employer": "employer account"
        }
        existing_type = collection_names.get(email_check["collection"], "account")
        return {"success": False, "message": f"Email already exists in {existing_type}."}
    
    if job_type_id == "FIND_JOB":
        user_col = collections("employee")
        job_type_enum = JobType.FIND_JOB
    elif job_type_id == "FIND_EMPLOYEE":
        user_col = collections("employer")
        job_type_enum = JobType.FIND_EMPLOYEE
    else:
        return {"success": False, "message": "Invalid job_type_id. Must be 'FIND_JOB' or 'FIND_EMPLOYEE'"}

    hashed_password = get_password_hash(password)

    new_user = {
        "email": email,
        "password": hashed_password, 
        "created_at": datetime.now(),
        "is_active": True
    }
    
    if job_type_enum:
        new_user["job_type"] = job_type_enum.value

    result = user_col.insert_one(new_user)
    
    if result.inserted_id:
        return {
            "success": True, 
            "message": "Account created successfully",
            "user_id": str(result.inserted_id) 
        }
    
    return {"success": False, "message": "Failed to create account"}

def find_user_by_id(user_id: str):
    try:
        for collection_name in ["users", "employee", "employer"]:
            user_col = collections(collection_name)
            user = user_col.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
                user.pop("password", None)
                return user
        return None
    except errors.InvalidId:
        return None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def login_service(email: str, password: str):
    for collection_name in ["users", "employee", "employer"]:
        user_col = collections(collection_name)
        user = user_col.find_one({"email": email})
        if user and verify_password(password, user["password"]):
            user.pop("password", None)
            user["_id"] = str(user["_id"])
            return user
    return None

def find_and_verify_by_pin(email: str, pin_code: str):
    otp_col = collections("otp_codes")
    otp_data = otp_col.find_one({"email": email})
    
    if not otp_data:
        return {"success": False, "message": "OTP not found or expired", "email": None}
    
    if datetime.now() > otp_data["expires_at"]:
        otp_col.delete_one({"email": email})
        return {"success": False, "message": "OTP expired", "email": None}
    
    if not pwd_context.verify(pin_code, otp_data["hashed_otp"]):
        return {"success": False, "message": "Invalid OTP code", "email": None}
    
    otp_col.delete_one({"email": email})
    return {"success": True, "message": "OTP verified", "email": email}

# 🎯 កែសម្រួល៖ បង្កើត និងផ្ញើ OTP ផ្ដោតទៅលើតែ Email មួយមុខគត់ (ដក Twilio ចេញទាំងស្រុង)
def create_otp(email: str):
    cleanup_expired_otps()
    
    user_found = False
    for collection_name in ["users", "employee", "employer"]:
        user_col = collections(collection_name)
        user = user_col.find_one({"email": email})
        if user:
            user_found = True
            break
    
    if not user_found:
        return {"success": False, "user_found": False, "message": "User not found"}
    
    otp_code = str(random.randint(1000, 9999))
    expires_at = datetime.now() + timedelta(minutes=10)
    hashed_otp = pwd_context.hash(otp_code)
    
    otp_col = collections("otp_codes")
    otp_col.delete_many({"email": email})
    
    otp_data = {
        "email": email,
        "hashed_otp": hashed_otp,
        "expires_at": expires_at,
        "created_at": datetime.now()
    }
    otp_col.insert_one(otp_data)
    
    sent_via = None
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if smtp_user and smtp_password:
            msg = MIMEText(f"Your 4-digit OTP code is: {otp_code}\nThis code expires in 10 minutes.")
            msg['Subject'] = 'Password Reset OTP'
            msg['From'] = smtp_user
            msg['To'] = email
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            sent_via = "email"
    except Exception as e:
        print(f"[ERROR] Email sending failed: {e}")
    
    return {
        "success": True if sent_via else False,
        "user_found": True,
        "sent_via": sent_via or "none",
        "message": f"OTP sent via {sent_via}" if sent_via else "Failed to send OTP due to connection error"
    }