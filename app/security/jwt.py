"""JWT Token Handling"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
import jwt
from dotenv import load_dotenv
import os

load_dotenv("working.env")


def _normalize_jwt_payload(value):
    """Recursively convert non-JSON-safe payload values before JWT encoding."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: _normalize_jwt_payload(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_jwt_payload(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_normalize_jwt_payload(v) for v in value)
    return value

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = _normalize_jwt_payload(data.copy())
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15)))
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        os.getenv("SECRET_KEY"),
        algorithm=os.getenv("ALGORITHM", "HS256")
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT access token"""
    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM", "HS256")]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
