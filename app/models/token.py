"""Token model."""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Token(Base):
    """Personal Access Token model."""
    
    __tablename__ = "tokens"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    token_prefix = Column(String(12), index=True, nullable=False)  # pat_ + 8 chars = 12 chars
    token_hash = Column(String, nullable=False)  # SHA-256 hash
    scopes = Column(JSON, nullable=False)  # List of scopes
    allowed_ips = Column(JSON, nullable=True)  # List of allowed IP addresses (null = no restriction)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tokens")
    audit_logs = relationship("AuditLog", back_populates="token", cascade="all, delete-orphan")