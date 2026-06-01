from datetime import datetime, timedelta, timezone
from bson import ObjectId

def create_refresh_token_model(user_id: ObjectId, token: str) -> dict:
    """រៀបចំទិន្នន័យ Refresh Token មុននឹង Save ចូល MongoDB"""
    return {
        "_id": ObjectId(),
        "user_id": user_id,
        "token": token,
        "is_revoked": False, # ប្រើសម្រាប់ Block (បញ្ឈប់) Token នេះនៅថ្ងៃក្រោយ
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "created_at": datetime.now(timezone.utc)
    }