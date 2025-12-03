"""Users endpoints (stub implementation)."""
from fastapi import APIRouter, Depends
from app.dependencies.auth import require_scope
from app.schemas.common import SuccessResponse
from app.schemas.auth import AuthContext
from app.core.permissions import Permission

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=SuccessResponse)
def get_current_user_info(
    auth_ctx: AuthContext = Depends(require_scope(Permission.USERS_READ))
):
    """Get current user information (requires users:read).
    
    This is a stub implementation showing permission verification.
    """
    return SuccessResponse(
        data={
            "endpoint": "/api/v1/users/me",
            "method": "GET",
            "required_scope": Permission.USERS_READ,
            "your_scopes": auth_ctx.user_scopes,
            "granted_by": auth_ctx.granted_by,
            "user_id": auth_ctx.user_id,
            "message": "This is a stub endpoint demonstrating permission control"
        }
    )


@router.put("/me", response_model=SuccessResponse)
def update_current_user(
    auth_ctx: AuthContext = Depends(require_scope(Permission.USERS_WRITE))
):
    """Update current user information (requires users:write).
    
    This is a stub implementation showing permission verification.
    """
    return SuccessResponse(
        data={
            "endpoint": "/api/v1/users/me",
            "method": "PUT",
            "required_scope": Permission.USERS_WRITE,
            "your_scopes": auth_ctx.user_scopes,
            "granted_by": auth_ctx.granted_by,
            "message": "This is a stub endpoint demonstrating permission control"
        }
    )