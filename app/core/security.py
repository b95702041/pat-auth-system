"""Security utilities for authentication and token management."""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def generate_pat_token() -> str:
    """Generate a Personal Access Token.
    
    Format: pat_<random_string>
    Returns: Full token string
    """
    # Generate random bytes and convert to hex
    random_bytes = secrets.token_bytes(settings.TOKEN_LENGTH)
    random_string = random_bytes.hex()
    
    # Add prefix
    token = f"{settings.TOKEN_PREFIX}{random_string}"
    return token


def hash_token(token: str) -> str:
    """Hash a token using SHA-256.
    
    Args:
        token: The full token string
        
    Returns:
        SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_hash(token: str, token_hash: str) -> bool:
    """Verify a token against its hash.
    
    Args:
        token: The full token string
        token_hash: The stored hash
        
    Returns:
        True if token matches hash, False otherwise
    """
    return hash_token(token) == token_hash


def get_token_prefix(token: str) -> str:
    """Get the prefix of a token for display/lookup.
    
    Args:
        token: The full token string
        
    Returns:
        First N characters of the token (including pat_ prefix)
    """
    prefix_length = len(settings.TOKEN_PREFIX) + settings.TOKEN_PREFIX_DISPLAY_LENGTH
    return token[:prefix_length]
