"""Pydantic Schemas for request/response validation"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: EmailStr
    is_admin: bool = False


class UserCreate(UserBase):
    """User creation schema"""
    password: str
    

class ClientCreate(BaseModel):
    """Client creation schema"""
    client_id: str
    client_name: str
    client_db_url: str
    client_email: Optional[EmailStr] = None

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str