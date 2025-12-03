"""Workspaces endpoints (stub implementation)."""
from fastapi import APIRouter, Depends
from app.dependencies.auth import require_scope
from app.schemas.common import SuccessResponse
from app.core.permissions import Permission

router = APIRouter(prefix="/api/v1/workspaces", tags=["Workspaces"])


@router.get("", response_model=SuccessResponse)
def list_workspaces(
    user_token: tuple = Depends(require_scope(Permission.WORKSPACES_READ))
):
    """List workspaces (requires workspaces:read).
    
    This is a stub implementation showing permission verification.
    """
    user, token = user_token
    
    return SuccessResponse(
        data={
            "endpoint": "/api/v1/workspaces",
            "method": "GET",
            "required_scope": Permission.WORKSPACES_READ,
            "your_scopes": token.scopes,
            "message": "This is a stub endpoint demonstrating permission control"
        }
    )


@router.post("", response_model=SuccessResponse)
def create_workspace(
    user_token: tuple = Depends(require_scope(Permission.WORKSPACES_WRITE))
):
    """Create workspace (requires workspaces:write).
    
    This is a stub implementation showing permission verification.
    """
    user, token = user_token
    
    return SuccessResponse(
        data={
            "endpoint": "/api/v1/workspaces",
            "method": "POST",
            "required_scope": Permission.WORKSPACES_WRITE,
            "your_scopes": token.scopes,
            "message": "This is a stub endpoint demonstrating permission control"
        }
    )


@router.delete("/{workspace_id}", response_model=SuccessResponse)
def delete_workspace(
    workspace_id: str,
    user_token: tuple = Depends(require_scope(Permission.WORKSPACES_DELETE))
):
    """Delete workspace (requires workspaces:delete).
    
    This is a stub implementation showing permission verification.
    """
    user, token = user_token
    
    return SuccessResponse(
        data={
            "endpoint": f"/api/v1/workspaces/{workspace_id}",
            "method": "DELETE",
            "required_scope": Permission.WORKSPACES_DELETE,
            "your_scopes": token.scopes,
            "message": "This is a stub endpoint demonstrating permission control"
        }
    )


@router.put("/{workspace_id}/settings", response_model=SuccessResponse)
def update_workspace_settings(
    workspace_id: str,
    user_token: tuple = Depends(require_scope(Permission.WORKSPACES_ADMIN))
):
    """Update workspace settings (requires workspaces:admin).
    
    This is a stub implementation showing permission verification.
    """
    user, token = user_token
    
    return SuccessResponse(
        data={
            "endpoint": f"/api/v1/workspaces/{workspace_id}/settings",
            "method": "PUT",
            "required_scope": Permission.WORKSPACES_ADMIN,
            "your_scopes": token.scopes,
            "message": "This is a stub endpoint demonstrating permission control"
        }
    )