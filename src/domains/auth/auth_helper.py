from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from src.core.mongo import collections
from src.core.security import verify_password

users_collection = collections("users")

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

async def validate_password_and_lockout(user: dict, password: str) -> bool:
    """
    Function នេះប្រើសម្រាប់ឆែក Password ផង និងគ្រប់គ្រងការ Block គណនីផង។
    អាចយកទៅប្រើបានទាំង Mobile Login និង Admin Login។
    """
    # 1. ឆែកមើលថាតើគណនីនេះកំពុងជាប់ Lock ដែរឬទេ?
    if user.get("locked_until") and user["locked_until"].replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
        time_left = user["locked_until"].replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)
        minutes = int(time_left.total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Your account is locked. Please try again after {minutes} minutes."
        )

    # 2. ឆែកមើលពាក្យសម្ងាត់
    if not verify_password(password, user["password_hash"]):
        # បើខុស បូកចំនួនដង (failed_login_attempts + 1)
        attempts = user.get("failed_login_attempts", 0) + 1
        update_data = {"failed_login_attempts": attempts}
        
        # បើវាយខុសដល់កំណត់ ធ្វើការ Lock គណនី
        if attempts >= MAX_LOGIN_ATTEMPTS:
            update_data["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
            
        await users_collection.update_one({"_id": user["_id"]}, {"$set": update_data})
        
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # 3. ករណី Login ជោគជ័យ ត្រូវ Reset ចំនួនវាយខុសឱ្យទៅជា 0 វិញ និងកត់ត្រាម៉ោង Login
    await users_collection.update_one(
        {"_id": user["_id"]}, 
        {"$set": {
            "failed_login_attempts": 0,
            "locked_until": None,
            "last_login_at": datetime.now(timezone.utc)
        }}
    )
    
    return True