"""Pydantic Schemas for request/response validation"""
import uuid

from pydantic import BaseModel, EmailStr, Field
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
    email: Optional[EmailStr] = None
    is_admin: bool = False
    

class ClientCreate(BaseModel):
    """Client creation schema"""
    client_id: str = Field(..., max_length=3, description="Unique 3-character client ID")
    name: str 
    email: Optional[EmailStr] = None
    db_url: str


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str

class OrderData(BaseModel):
    """Base order data schema"""
    client_id: uuid.UUID
    customer_id: str
    customer_name: str
    company_id: str = Field(max_length=3, description="Unique 3-character client ID")
    location_id: Optional[str] = None


class SalesOrderCreate(OrderData):
    """Sales order header creation schema"""
    # Define fields for sales order header creation as needed
    sales_order_count: int = 5
    lower_item_count: int = 1
    upper_item_count: int = 25


class PurchaseOrderCreate(BaseModel):
    """Purchase order header creation schema"""
    client_id: uuid.UUID
    company_id: str
    location_id: int
    items: list[dict]
    purchase_order_type: Optional[str] = None