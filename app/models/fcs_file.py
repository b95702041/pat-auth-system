"""FCS file model."""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from datetime import datetime
from app.database import Base


class FCSFile(Base):
    """FCS file metadata model."""
    
    __tablename__ = "fcs_files"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    total_events = Column(Integer, nullable=False)
    total_parameters = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
