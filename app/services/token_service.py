"""Token service for PAT management."""
import uuid
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.token import Token
from app.schemas.token import TokenCreate
from app.core.security import generate_pat_token, hash_token, get_token_prefix


class TokenService:
    """Service for Personal Access Token operations."""
    
    @staticmethod
    def create_token(db: Session, user_id: str, token_data: TokenCreate) -> tuple[Token, str]:
        """Create a new Personal Access Token.
        
        Args:
            db: Database session
            user_id: User ID
            token_data: Token creation data
            
        Returns:
            Tuple of (token_model, full_token_string)
        """
        # Generate token
        full_token = generate_pat_token()
        token_hash = hash_token(full_token)
        token_prefix = get_token_prefix(full_token)
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=token_data.expires_in_days)
        
        # Create token record
        token = Token(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=token_data.name,
            token_prefix=token_prefix,
            token_hash=token_hash,
            scopes=token_data.scopes,
            expires_at=expires_at
        )
        
        db.add(token)
        db.commit()
        db.refresh(token)
        
        return token, full_token
    
    @staticmethod
    def list_tokens(db: Session, user_id: str) -> List[Token]:
        """List all tokens for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of tokens
        """
        return db.query(Token).filter(Token.user_id == user_id).all()
    
    @staticmethod
    def get_token(db: Session, user_id: str, token_id: str) -> Token:
        """Get a specific token.
        
        Args:
            db: Database session
            user_id: User ID
            token_id: Token ID
            
        Returns:
            Token
            
        Raises:
            HTTPException: If token not found
        """
        token = db.query(Token).filter(
            Token.id == token_id,
            Token.user_id == user_id
        ).first()
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found"
            )
        
        return token
    
    @staticmethod
    def revoke_token(db: Session, user_id: str, token_id: str) -> Token:
        """Revoke a token.
        
        Args:
            db: Database session
            user_id: User ID
            token_id: Token ID
            
        Returns:
            Revoked token
            
        Raises:
            HTTPException: If token not found
        """
        token = TokenService.get_token(db, user_id, token_id)
        token.is_revoked = True
        db.commit()
        db.refresh(token)
        
        return token
