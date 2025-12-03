"""Users endpoints (stub implementation)."""
from fastapi import APIRouter, Depends
from app.dependencies.auth import require_scope
from app.schemas.common import SuccessResponse
from app.core.permissions import Permission

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=SuccessResponse)
async def get_current_user_info(
    user_token: tuple = Depends(require_scope(Permission.USERS_READ))
):
    """Get current user information (requires users:read).
    
    This is a stub implementation showing permission verification.
    """
    user, token = user_token
    
    return SuccessResponse(
        data={
            "endpoint": "/api/v1/users/me",
            "method": "GET",
            "required_scope": Permission.USERS_READ,
            "your_scopes": token.scopes,
            "user_id": user.id,
            "username": user.username,
            "message": "This is a stub endpoint demonstrating permission control"
        }
    )


@router.put("/me", response_model=SuccessResponse)
async def update_current_user(
    user_token: tuple = Depends(require_scope(Permission.USERS_WRITE))
):
    """Update current user information (requires users:write).
    
    This is a stub implementation showing permission verification.
    """
    user, token = user_token
    
    return SuccessResponse(
        data={
            "endpoint": "/api/v1/users/me",
            "method": "PUT",
            "required_scope": Permission.USERS_WRITE,
            "your_scopes": token.scopes,
            "message": "This is a stub endpoint demonstrating permission control"
        }
    )
