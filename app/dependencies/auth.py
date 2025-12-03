"""Authentication and authorization dependencies."""
from typing import Callable
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session
from datetime import datetime

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.token import Token
from app.schemas.user import TokenData
from app.core.security import verify_token_hash, verify_token
from app.core.permissions import check_permission
from app.services.audit_service import log_token_usage

settings = get_settings()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, username=payload.get("username"))
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    return user


def get_current_user_from_pat(
    request: Request,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> tuple[User, Token]:
    """Get current user from Personal Access Token.
    
    Returns:
        Tuple of (User, Token)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token_string = authorization.replace("Bearer ", "")
    
    # Get token prefix for lookup
    token_prefix = token_string[:len(settings.TOKEN_PREFIX) + settings.TOKEN_PREFIX_DISPLAY_LENGTH]
    
    # Find tokens with matching prefix
    tokens = db.query(Token).filter(Token.token_prefix == token_prefix).all()
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Verify hash
    valid_token = None
    for token in tokens:
        if verify_token_hash(token_string, token.token_hash):
            valid_token = token
            break
    
    if not valid_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Check if token is revoked
    if valid_token.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked"
        )
    
    # Check if token is expired
    if valid_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    
    # Update last used time
    valid_token.last_used_at = datetime.utcnow()
    db.commit()
    
    # Get user
    user = db.query(User).filter(User.id == valid_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user, valid_token


def require_scope(required_scope: str) -> Callable:
    """Dependency factory for checking required scope.
    
    Args:
        required_scope: The scope required for this endpoint
        
    Returns:
        Dependency function that checks scope
    """
    def scope_checker(
        request: Request,
        user_token: tuple[User, Token] = Depends(get_current_user_from_pat),
        db: Session = Depends(get_db)
    ) -> tuple[User, Token]:
        user, token = user_token
        
        # Check permission
        has_permission = check_permission(required_scope, token.scopes)
        
        # Log the attempt
        client_ip = request.client.host if request.client else "unknown"
        log_token_usage(
            db=db,
            token_id=token.id,
            ip_address=client_ip,
            method=request.method,
            endpoint=request.url.path,
            status_code=200 if has_permission else 403,
            authorized=has_permission,
            reason=None if has_permission else "Insufficient permissions"
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": "Forbidden",
                    "data": {
                        "required_scope": required_scope,
                        "your_scopes": token.scopes
                    }
                }
            )
        
        return user, token
    
    return scope_checker