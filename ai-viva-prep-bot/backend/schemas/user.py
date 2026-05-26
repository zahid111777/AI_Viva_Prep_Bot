from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    university: Optional[str] = None
    department: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    university: Optional[str] = None
    department: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    university: Optional[str] = None
    department: Optional[str] = None
    preferred_provider: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    role: str
