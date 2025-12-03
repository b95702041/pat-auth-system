"""Audit log model."""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class AuditLog(Base):
    """Audit log for token usage."""
    
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, index=True)
    token_id = Column(String, ForeignKey("tokens.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String, nullable=False)
    method = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    authorized = Column(Boolean, nullable=False)
    reason = Column(String, nullable=True)  # Error reason if not authorized
    
    # Relationships
    token = relationship("Token", back_populates="audit_logs")
