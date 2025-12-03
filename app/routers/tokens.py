"""Token management endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.token import TokenCreate, TokenResponse, TokenListItem, TokenDetailResponse
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse
from app.schemas.common import SuccessResponse
from app.services.token_service import TokenService
from app.services.audit_service import get_token_logs
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/v1/tokens", tags=["Tokens"])


@router.post("", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_token(
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
async def list_tokens(
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
async def get_token(
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
async def revoke_token(
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
async def get_token_audit_logs(
    token_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs for a specific token.
    
    Args:
        token_id: Token ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Audit logs for the token
    """
    # Verify token belongs to user
    token = TokenService.get_token(db, current_user.id, token_id)
    
    # Get logs
    token, logs = get_token_logs(db, token_id)
    
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
            "total_logs": len(log_list),
            "logs": log_list
        }
    )
