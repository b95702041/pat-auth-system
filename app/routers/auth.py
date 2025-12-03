"""Authentication endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.common import SuccessResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user information
    """
    user = UserService.create_user(db, user_data)
    
    return SuccessResponse(
        data={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        }
    )


@router.post("/login", response_model=SuccessResponse)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login and get JWT token.
    
    Args:
        login_data: Login credentials
        db: Database session
        
    Returns:
        JWT access token
    """
    user, access_token = UserService.authenticate_user(db, login_data)
    
    return SuccessResponse(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
    )