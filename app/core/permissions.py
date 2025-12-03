"""Permission management with hierarchical scopes."""
from enum import Enum
from typing import List, Dict


class Permission(str, Enum):
    """Permission levels for different resources."""
    
    # Workspaces permissions (high to low)
    WORKSPACES_ADMIN = "workspaces:admin"
    WORKSPACES_DELETE = "workspaces:delete"
    WORKSPACES_WRITE = "workspaces:write"
    WORKSPACES_READ = "workspaces:read"
    
    # Users permissions (high to low)
    USERS_WRITE = "users:write"
    USERS_READ = "users:read"
    
    # FCS permissions (high to low)
    FCS_ANALYZE = "fcs:analyze"
    FCS_WRITE = "fcs:write"
    FCS_READ = "fcs:read"


# Define hierarchical permission structure
# Higher permissions automatically include lower ones within the same resource
RESOURCE_PERMISSIONS: Dict[str, List[str]] = {
    "workspaces": [
        Permission.WORKSPACES_ADMIN,
        Permission.WORKSPACES_DELETE,
        Permission.WORKSPACES_WRITE,
        Permission.WORKSPACES_READ,
    ],
    "users": [
        Permission.USERS_WRITE,
        Permission.USERS_READ,
    ],
    "fcs": [
        Permission.FCS_ANALYZE,
        Permission.FCS_WRITE,
        Permission.FCS_READ,
    ],
}


def get_resource_from_scope(scope: str) -> str:
    """Extract resource name from scope string.
    
    Args:
        scope: Scope string like "workspaces:read"
        
    Returns:
        Resource name like "workspaces"
    """
    return scope.split(":")[0]


def get_granted_permissions(scope: str) -> List[str]:
    """Get all permissions granted by a scope (including lower permissions).
    
    Args:
        scope: The scope that was granted (e.g., "workspaces:write")
        
    Returns:
        List of all permissions granted by this scope
    """
    resource = get_resource_from_scope(scope)
    resource_hierarchy = RESOURCE_PERMISSIONS.get(resource, [])
    
    if scope not in resource_hierarchy:
        return [scope]
    
    # Find the position of this scope in hierarchy
    scope_index = resource_hierarchy.index(scope)
    
    # Return this scope and all lower scopes
    return resource_hierarchy[scope_index:]


def check_permission(required_scope: str, user_scopes: List[str]) -> bool:
    """Check if user has required permission.
    
    Hierarchical rules:
    - Higher permissions include lower ones within same resource
    - Permissions do NOT cross resources
    
    Args:
        required_scope: The permission required (e.g., "workspaces:read")
        user_scopes: List of scopes the user has
        
    Returns:
        True if user has required permission, False otherwise
    """
    # Get resource of required scope
    required_resource = get_resource_from_scope(required_scope)
    
    # Check each user scope
    for user_scope in user_scopes:
        user_resource = get_resource_from_scope(user_scope)
        
        # Skip if different resource
        if user_resource != required_resource:
            continue
        
        # Get all permissions granted by user's scope
        granted_permissions = get_granted_permissions(user_scope)
        
        # Check if required scope is granted
        if required_scope in granted_permissions:
            return True
    
    return False


def get_highest_scope(scopes: List[str], resource: str) -> str:
    """Get the highest scope for a resource.
    
    Args:
        scopes: List of scopes
        resource: Resource name
        
    Returns:
        Highest scope for the resource, or empty string if none
    """
    resource_hierarchy = RESOURCE_PERMISSIONS.get(resource, [])
    
    for scope in resource_hierarchy:
        if scope in scopes:
            return scope
    
    return ""
