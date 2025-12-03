"""Authentication schemas."""
from pydantic import BaseModel
from typing import List


class AuthContext(BaseModel):
    """Authentication context for PAT-protected endpoints."""
    token_id: str
    user_id: str
    required_scope: str
    granted_by: str  # The actual scope that granted the permission
    user_scopes: List[str]
    
    class Config:
        from_attributes = True