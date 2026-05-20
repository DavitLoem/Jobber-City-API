from datetime import datetime, timedelta
from typing import Collection, Optional
import random
import smtplib
import os
from email.mime.text import MIMEText
from bson import ObjectId, errors
from src.config.mongo import collections # import មុខងារភ្ជាប់ DB
from src.model.auth import JobType
from passlib.context import CryptContext
from twilio.rest import Client


def get_all_job_types():
    """ទាញយកប្រភេទការងារទាំងអស់សម្រាប់បង្ហាញក្នុង UI"""
    return [
        {"id": "FIND_JOB", "title": JobType.FIND_JOB.value, "description": "I want to find a job for me."},
        {"id": "FIND_EMPLOYEE", "title": JobType.FIND_EMPLOYEE.value, "description": "I want to find employees."}
    ]

# កំណត់ការប្រើប្រាស់ bcrypt សម្រាប់ hash password
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


def check_email_uniqueness_for_update(email: str, exclude_user_id: str = None):
    collections_to_check = ["users", "employee", "employer"]
    
    for collection_name in collections_to_check:
        current_col = collections(collection_name)
        query = {"email": email}
        
        # If excluding a user ID, add that to the query
        if exclude_user_id:
            try:
                query["_id"] = {"$ne": ObjectId(exclude_user_id)}
            except errors.InvalidId:
                # If the ID is invalid, just check without exclusion
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
    # ១. ឆែកមើល email ស្ទួននៅក្នុងគ្រប់ collections ដើម្បីបង្ការការប្រើប្រាស់ email ដដែលច្រើនដង
    email_check = check_email_exists_across_all_collections(email)
    if email_check["exists"]:
        # Provide specific message about which collection the email exists in
        collection_names = {
            "users": "basic user account",
            "employee": "employee account", 
            "employer": "employer account"
        }
        existing_type = collection_names.get(email_check["collection"], "account")
        return {"success": False, "message": f"Email already exists in {existing_type}. Each email can only be used for one account type."}
    
    # ២. កំណត់ collection តាមរយៈ job_type_id
    if job_type_id == "FIND_JOB":
        user_col = collections("employee")
        job_type_enum = JobType.FIND_JOB
    elif job_type_id == "FIND_EMPLOYEE":
        user_col = collections("employer")
        job_type_enum = JobType.FIND_EMPLOYEE
    else:
        return {"success": False, "message": "Invalid job_type_id. Must be 'FIND_JOB' or 'FIND_EMPLOYEE'"}

    # ៣. បំប្លែង password ឱ្យទៅជា hash (ដើម្បីសុវត្ថិភាព)
    hashed_password = get_password_hash(password)

    # ៤. រៀបចំទិន្នន័យសម្រាប់បញ្ចូលទៅ DB
    new_user = {
        "email": email,
        "password": hashed_password, # ប្រើ password ដែល hash រួច
        "created_at": datetime.now(),
        "is_active": True
    }
    
    if job_type_enum:
        new_user["job_type"] = job_type_enum.value

    # ៥. បញ្ចូលទៅក្នុង MongoDB
    result = user_col.insert_one(new_user)
    
    if result.inserted_id:
        # Return ID ត្រឡប់ទៅវិញ ដើម្បីឱ្យ API ងាយស្រួលប្រើបន្ត
        return {
            "success": True, 
            "message": "Account created successfully",
            "user_id": str(result.inserted_id) 
        }
    
    return {"success": False, "message": "Failed to create account"}


def find_user_by_id(user_id: str):
    try:
        # Check in users collection first
        user_col = collections("users")
        user = user_col.find_one({"_id": ObjectId(user_id)})

        if user:
            user["_id"] = str(user["_id"])
            if "password" in user:
                del user["password"]
            return user

        # Check in employee collection
        employee_col = collections("employee")
        user = employee_col.find_one({"_id": ObjectId(user_id)})

        if user:
            user["_id"] = str(user["_id"])
            if "password" in user:
                del user["password"]
            return user

        # Check in employer collection
        employer_col = collections("employer")
        user = employer_col.find_one({"_id": ObjectId(user_id)})

        if user:
            user["_id"] = str(user["_id"])
            if "password" in user:
                del user["password"]
            return user
                
        return None
    except errors.InvalidId:
        # បើ ID ផ្ញើមកខុសទម្រង់ មិនឱ្យ Crash ទេ គឺឱ្យ return None
        return None

  


def forgot_password(email: str = None, phone: str = None):
    # ស្វែងរក User ដោយប្រើ Email "ឬ" Phone (ប្រើ $or operator របស់ MongoDB)
    query = {"$or": []}
    if email:
        query["$or"].append({"email": email})
    if phone:
        query["$or"].append({"phone": phone})
    
    # បើអត់មានទាំងពីរ មិនបាច់រកទេ
    if not query["$or"]:
        return None

    # Check in users collection first
    user_col = collections("users")
    user = user_col.find_one(query)

    if user:
        user["_id"] = str(user["_id"])
        user.pop("password", None)
        return user

    # Check in employee collection
    employee_col = collections("employee")
    user = employee_col.find_one(query)

    if user:
        user["_id"] = str(user["_id"])
        user.pop("password", None)
        return user

    # Check in employer collection
    employer_col = collections("employer")
    user = employer_col.find_one(query)

    if user:
        user["_id"] = str(user["_id"])
        user.pop("password", None)
        return user
    
    return None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def login_service(email: str, password: str):
    # Check in users collection first (for users who haven't completed profile)
    user_col = collections("users")
    user = user_col.find_one({"email": email})
    
    if user and verify_password(password, user["password"]):
        user.pop("password", None)
        user["_id"] = str(user["_id"])
        return user
    
    # Check in employee collection
    employee_col = collections("employee")
    user = employee_col.find_one({"email": email})
    
    if user and verify_password(password, user["password"]):
        user.pop("password", None)
        user["_id"] = str(user["_id"])
        return user
    
    # Check in employer collection
    employer_col = collections("employer")
    user = employer_col.find_one({"email": email})
    
    if user and verify_password(password, user["password"]):
        user.pop("password", None)
        user["_id"] = str(user["_id"])
        return user
    
    return None


def find_and_verify_by_pin(email: str, pin_code: str):
    # Check MongoDB for OTP
    otp_col = collections("otp_codes")
    otp_data = otp_col.find_one({"email": email})
    
    if not otp_data:
        return {"success": False, "message": "OTP not found or expired", "email": None}
    
    # Check if expired
    if datetime.now() > otp_data["expires_at"]:
        otp_col.delete_one({"email": email})
        return {"success": False, "message": "OTP expired", "email": None}
    
    # Verify code against hashed OTP
    if not pwd_context.verify(pin_code, otp_data["hashed_otp"]):
        return {"success": False, "message": "Invalid OTP code", "email": None}
    
    # Success - delete OTP from MongoDB
    otp_col.delete_one({"email": email})
    return {"success": True, "message": "OTP verified", "email": email}




def create_otp(email: str = None, phone: str = None):
    # Cleanup expired OTPs first
    cleanup_expired_otps()
    
    query = {}
    if email:
        query["email"] = email
    elif phone:
        query["phone"] = phone
    
    if not query:
        return {"success": False, "user_found": False, "message": "No identity provided"}
    
    # Check in users collection first
    user_col = collections("users")
    user = user_col.find_one(query)
    
    if not user:
        # Check in employee collection
        employee_col = collections("employee")
        user = employee_col.find_one(query)
    
    if not user:
        # Check in employer collection
        employer_col = collections("employer")
        user = employer_col.find_one(query)
    
    if not user:
        return {"success": False, "user_found": False, "message": "User not found"}
    
    # Generate 4-digit OTP
    otp_code = str(random.randint(1000, 9999))
    expires_at = datetime.now() + timedelta(minutes=10)
    
    # Hash the OTP for secure storage
    hashed_otp = pwd_context.hash(otp_code)
    
    # Store OTP in MongoDB with hashed code
    otp_col = collections("otp_codes")
    otp_data = {
        "email": email,
        "phone": phone,
        "hashed_otp": hashed_otp,
        "expires_at": expires_at,
        "created_at": datetime.now()
    }
    
    # Delete any existing OTP for this user
    if email:
        otp_col.delete_many({"email": email})
    elif phone:
        otp_col.delete_many({"phone": phone})
    
    # Insert new OTP
    otp_col.insert_one(otp_data)
    
    sent_via = None
    
    # Send via email if provided
    if email:
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
            import traceback
            traceback.print_exc()
    
    # Send via SMS using Twilio Verify API
    if phone and not sent_via:
        try:
            twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
            twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
            verify_service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")
            
            if twilio_sid and twilio_token and verify_service_sid:
                client = Client(twilio_sid, twilio_token)
                
                # Format phone number (ensure +855 for Cambodia)
                to_phone = phone if phone.startswith("+") else f"+855{phone.lstrip('0')}"
                
                # Use Twilio Verify API to send OTP
                verification = client.verify.v2.services(verify_service_sid) \
                    .verifications \
                    .create(to=to_phone, channel='sms')
                
                sent_via = "phone"
            else:
                print(f"[ERROR] Missing Twilio credentials: SID={twilio_sid}, Token={'set' if twilio_token else 'missing'}, Service={verify_service_sid}")
        except Exception as e:
            print(f"[ERROR] SMS sending failed: {e}")
            import traceback
            traceback.print_exc()
    
    return {
        "success": True,
        "user_found": True,
        "sent_via": sent_via or "none",
        "message": f"OTP sent via {sent_via}" if sent_via else "Failed to send OTP"
    }

