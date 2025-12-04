"""Token schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class TokenCreate(BaseModel):
    """Schema for creating a PAT."""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[str] = Field(..., min_items=1)
    expires_in_days: int = Field(..., ge=1, le=365)


class TokenRegenerate(BaseModel):
    """Schema for regenerating a PAT."""
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Optional: extend expiration time")


class TokenResponse(BaseModel):
    """Schema for token creation response (includes full token)."""
    id: str
    name: str
    token: str  # Full token, shown only once
    scopes: List[str]
    created_at: datetime
    expires_at: datetime
    
    class Config:
        from_attributes = True


class TokenListItem(BaseModel):
    """Schema for token list item (no full token)."""
    id: str
    name: str
    token_prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: datetime
    last_used_at: Optional[datetime]
    is_revoked: bool
    
    class Config:
        from_attributes = True


class TokenListResponse(BaseModel):
    """Schema for token list response."""
    tokens: List[TokenListItem]
    total: int


class TokenDetailResponse(BaseModel):
    """Schema for token detail response."""
    id: str
    name: str
    token_prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: datetime
    last_used_at: Optional[datetime]
    is_revoked: bool
    
    class Config:
        from_attributes = True