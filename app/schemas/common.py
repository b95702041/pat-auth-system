"""Common schemas."""
from pydantic import BaseModel
from typing import Any, Optional


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    data: Any


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    message: Optional[str] = None
    data: Optional[Any] = None
