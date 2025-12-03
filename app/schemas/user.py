"""User schemas."""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """Schema for JWT token data."""
    user_id: str
    username: str