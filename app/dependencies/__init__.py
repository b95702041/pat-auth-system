"""Dependencies for FastAPI."""
from app.dependencies.auth import (
    get_current_user,
    get_current_user_from_pat,
    require_scope,
)

__all__ = [
    "get_current_user",
    "get_current_user_from_pat",
    "require_scope",
]
