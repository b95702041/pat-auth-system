"""Permission management with hierarchical scopes."""
from enum import Enum
from typing import List, Dict, Tuple, Optional


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


# Define hierarchical permission structure with numeric levels
PERMISSION_HIERARCHY: Dict[str, Dict[str, int]] = {
    "workspaces": {
        "admin": 4,
        "delete": 3,
        "write": 2,
        "read": 1
    },
    "users": {
        "write": 2,
        "read": 1
    },
    "fcs": {
        "analyze": 3,
        "write": 2,
        "read": 1
    }
}


# Define hierarchical permission structure (ordered list, high to low)
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


def validate_scope(scope: str) -> bool:
    """Validate if a single scope is valid.
    
    Args:
        scope: Scope string like "workspaces:read"
        
    Returns:
        True if valid, False otherwise
    """
    if not scope or ":" not in scope:
        return False
    
    parts = scope.split(":")
    if len(parts) != 2:
        return False
    
    resource, action = parts
    
    # Check if resource exists
    if resource not in PERMISSION_HIERARCHY:
        return False
    
    # Check if action exists for this resource
    if action not in PERMISSION_HIERARCHY[resource]:
        return False
    
    return True


def validate_scopes(scopes: List[str]) -> bool:
    """Validate if all scopes in the list are valid.
    
    Args:
        scopes: List of scope strings
        
    Returns:
        True if all are valid, False otherwise
    """
    if not scopes:
        return False
    
    return all(validate_scope(scope) for scope in scopes)


def get_all_valid_scopes() -> List[str]:
    """Get list of all valid scopes.
    
    Returns:
        List of all valid scope strings
    """
    all_scopes = []
    for resource, actions in PERMISSION_HIERARCHY.items():
        for action in actions.keys():
            all_scopes.append(f"{resource}:{action}")
    return sorted(all_scopes)


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


def check_permission(user_scopes: List[str], required_scope: str) -> Tuple[bool, Optional[str]]:
    """Check if user has required permission.
    
    Hierarchical rules:
    - Higher permissions include lower ones within same resource
    - Permissions do NOT cross resources
    
    Args:
        user_scopes: List of scopes the user has
        required_scope: The permission required (e.g., "workspaces:read")
        
    Returns:
        Tuple of (is_authorized, granted_by_scope)
        - (True, "workspaces:admin") if authorized by workspaces:admin
        - (False, None) if not authorized
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
            return True, user_scope
    
    return False, None


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