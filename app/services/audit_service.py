"""Audit service for logging token usage."""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.token import Token


async def log_token_usage(
    db: Session,
    token_id: str,
    ip_address: str,
    method: str,
    endpoint: str,
    status_code: int,
    authorized: bool,
    reason: Optional[str] = None
) -> AuditLog:
    """Log token usage.
    
    Args:
        db: Database session
        token_id: Token ID
        ip_address: Client IP address
        method: HTTP method
        endpoint: API endpoint
        status_code: Response status code
        authorized: Whether the request was authorized
        reason: Reason for failure (if not authorized)
        
    Returns:
        Created audit log entry
    """
    log = AuditLog(
        id=str(uuid.uuid4()),
        token_id=token_id,
        ip_address=ip_address,
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        authorized=authorized,
        reason=reason
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    return log


def get_token_logs(db: Session, token_id: str, limit: int = 100) -> tuple[Token, List[AuditLog]]:
    """Get audit logs for a token.
    
    Args:
        db: Database session
        token_id: Token ID
        limit: Maximum number of logs to return
        
    Returns:
        Tuple of (token, logs)
    """
    token = db.query(Token).filter(Token.id == token_id).first()
    if not token:
        return None, []
    
    logs = db.query(AuditLog).filter(
        AuditLog.token_id == token_id
    ).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()
    
    return token, logs
