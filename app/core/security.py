from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
import bcrypt
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    # bcrypt requires bytes
    # Ensure hashed_password is bytes (it might come as str from DB)
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def get_password_hash(password: str) -> str:
    # bcrypt returns bytes, we decode to store as string
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
