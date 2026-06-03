import os
import jwt
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status

# 1. រៀបចំ Argon2 សម្រាប់ Hash Password
ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


# 2. រៀបចំមុខងារទាក់ទងនឹង JWT Token
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # អាយុកាលនៃ Access Token
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict) -> str:
    """ប្រើសម្រាប់បង្កើត Token ថ្មីពេលគាត់ Login ជោគជ័យ"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire}) # exp គឺសម្រាប់កំណត់ម៉ោងផុតកំណត់
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """ប្រើសម្រាប់បង្កើតសោរអាយុវែង ដើម្បីយកមកដូរយក Access Token ថ្មី"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire}) 
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """ប្រើសម្រាប់បកប្រែ (Decode) Token ដែល Client បោះមកឱ្យ"""
    try:
        # បើ Token ផុតកំណត់ ឬ ខុស Secret Key វានឹងលោតចូល except
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token has expired" # បើ Token ផុតកំណត់ (Expired)
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token" # បើ Token មិនត្រឹមត្រូវ ឬ ត្រូវបានបំលែងដោយអ្នកដទៃ
        )