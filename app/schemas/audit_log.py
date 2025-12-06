"""Audit log schemas."""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional


class AuditLogResponse(BaseModel):
    """Schema for audit log entry."""
    timestamp: datetime
    ip: str
    method: str
    endpoint: str
    status_code: int
    authorized: bool
    reason: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """Schema for audit log list response."""
    token_id: str
    token_name: str
    total_logs: int
    logs: List[AuditLogResponse]