"""User service for user management."""
import uuid
from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.core.security import get_password_hash, verify_password, create_access_token


class UserService:
    """Service for user operations."""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user.
        
        Args:
            db: Database session
            user_data: User creation data
            
        Returns:
            Created user
            
        Raises:
            HTTPException: If username or email already exists
        """
        # Check if username exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password)
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin) -> tuple[User, str]:
        """Authenticate user and return JWT token.
        
        Args:
            db: Database session
            login_data: Login credentials
            
        Returns:
            Tuple of (user, jwt_token)
            
        Raises:
            HTTPException: If authentication fails
        """
        # Find user
        user = db.query(User).filter(User.username == login_data.username).first()
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Create JWT token
        token_data = {
            "user_id": user.id,
            "username": user.username
        }
        access_token = create_access_token(token_data)
        
        return user, access_token
