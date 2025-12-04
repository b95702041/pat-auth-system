"""Token management endpoints."""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.token import TokenCreate, TokenRegenerate, TokenResponse, TokenListItem, TokenDetailResponse
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse
from app.schemas.common import SuccessResponse
from app.services.token_service import TokenService
from app.services.audit_service import get_token_logs
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/v1/tokens", tags=["Tokens"])


@router.post("", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def create_token(
    token_data: TokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new Personal Access Token.
    
    Args:
        token_data: Token creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created token with full token string (shown only once)
    """
    token, full_token = TokenService.create_token(db, current_user.id, token_data)
    
    return SuccessResponse(
        data={
            "id": token.id,
            "name": token.name,
            "token": full_token,  # Full token shown only once
            "scopes": token.scopes,
            "created_at": token.created_at.isoformat(),
            "expires_at": token.expires_at.isoformat()
        }
    )


@router.get("", response_model=SuccessResponse)
def list_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all Personal Access Tokens for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of tokens (with prefix only, no full token)
    """
    tokens = TokenService.list_tokens(db, current_user.id)
    
    token_list = [
        {
            "id": token.id,
            "name": token.name,
            "token_prefix": token.token_prefix,
            "scopes": token.scopes,
            "created_at": token.created_at.isoformat(),
            "expires_at": token.expires_at.isoformat(),
            "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
            "is_revoked": token.is_revoked
        }
        for token in tokens
    ]
    
    return SuccessResponse(
        data={
            "tokens": token_list,
            "total": len(token_list)
        }
    )


@router.get("/{token_id}", response_model=SuccessResponse)
def get_token(
    token_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific token.
    
    Args:
        token_id: Token ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Token details
    """
    token = TokenService.get_token(db, current_user.id, token_id)
    
    return SuccessResponse(
        data={
            "id": token.id,
            "name": token.name,
            "token_prefix": token.token_prefix,
            "scopes": token.scopes,
            "created_at": token.created_at.isoformat(),
            "expires_at": token.expires_at.isoformat(),
            "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
            "is_revoked": token.is_revoked
        }
    )


@router.delete("/{token_id}", response_model=SuccessResponse)
def revoke_token(
    token_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a Personal Access Token.
    
    Args:
        token_id: Token ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    token = TokenService.revoke_token(db, current_user.id, token_id)
    
    return SuccessResponse(
        data={
            "message": "Token revoked successfully",
            "token_id": token.id
        }
    )


@router.get("/{token_id}/logs", response_model=SuccessResponse)
def get_token_audit_logs(
    token_id: str,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs for a specific token.
    
    Args:
        token_id: Token ID
        limit: Maximum number of logs to return (1-1000, default 50)
        offset: Offset for pagination (default 0)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Audit logs for the token
    """
    # Verify token belongs to user
    token = TokenService.get_token(db, current_user.id, token_id)
    
    # Get all logs for count
    all_logs = db.query(AuditLog).filter(
        AuditLog.token_id == token_id
    ).order_by(AuditLog.timestamp.desc()).all()
    
    # Apply pagination
    logs = all_logs[offset:offset+limit]
    
    log_list = [
        {
            "timestamp": log.timestamp.isoformat(),
            "ip": log.ip_address,
            "method": log.method,
            "endpoint": log.endpoint,
            "status_code": log.status_code,
            "authorized": log.authorized,
            "reason": log.reason
        }
        for log in logs
    ]
    
    return SuccessResponse(
        data={
            "token_id": token.id,
            "token_name": token.name,
            "total_logs": len(all_logs),
            "limit": limit,
            "offset": offset,
            "logs": log_list
        }
    )


@router.post("/{token_id}/regenerate", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
def regenerate_token(
    token_id: str,
    regenerate_data: TokenRegenerate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate a token with new token string.
    
    Keeps the same name and scopes but generates a new token string.
    The old token is automatically invalidated (new hash replaces old one).
    
    Args:
        token_id: Token ID to regenerate
        regenerate_data: Optional expiration extension
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Regenerated token with new full token string (shown only once)
        
    Raises:
        404: Token not found
        400: Token is already revoked
    """
    # Default to None if no body provided
    expires_in_days = None
    if regenerate_data and regenerate_data.expires_in_days is not None:
        expires_in_days = regenerate_data.expires_in_days
    
    # Regenerate token
    token, new_full_token = TokenService.regenerate_token(
        db, 
        current_user.id, 
        token_id,
        expires_in_days
    )
    
    return SuccessResponse(
        data={
            "id": token.id,
            "name": token.name,
            "token": new_full_token,  # Full token shown only once
            "scopes": token.scopes,
            "created_at": token.created_at.isoformat(),
            "expires_at": token.expires_at.isoformat()
        }
    )