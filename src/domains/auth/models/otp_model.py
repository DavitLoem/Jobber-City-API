from datetime import datetime, timedelta, timezone
from bson import ObjectId

def create_otp_model(user_id: ObjectId, email: str, otp_hash: str, purpose: str = "register") -> dict:
    """
    បង្កើតទម្រង់ OTP សម្រាប់បញ្ចូលទៅក្នុង MongoDB។
    កំណត់អាយុកាល (TTL) ត្រឹម 5 នាទី។
    """
    # កំណត់ម៉ោងផុតកំណត់ = ម៉ោងបច្ចុប្បន្ន + 5 នាទី
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    return {
        "_id": ObjectId(),
        "user_id": user_id,
        "email": email,
        "otp_hash": otp_hash, # រក្សាទុកជាទម្រង់ Hash ដើម្បីសុវត្ថិភាព
        "purpose": purpose,
        "is_used": False,
        "attempts": 0,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    }