"""
Feedback database model.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from database.connection import Base
import enum


class FeedbackType(str, enum.Enum):
    """Feedback type enumeration."""
    BUG = "bug"
    IMPROVEMENT = "improvement"


class FeedbackStatus(str, enum.Enum):
    """Feedback status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class FeedbackPriority(str, enum.Enum):
    """Feedback priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Feedback(Base):
    __tablename__ = "feedback"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core Fields
    type = Column(SQLEnum(FeedbackType), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(FeedbackStatus), nullable=False, default=FeedbackStatus.OPEN, index=True)
    priority = Column(SQLEnum(FeedbackPriority), nullable=True)
    
    # Submitter Information
    submitted_by = Column(String, nullable=True)  # Email or name (optional for public)
    
    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False, server_default=func.now(), index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Resolution Information
    resolution_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)  # Internal only, not exposed in public API
    
    # Metadata (renamed from 'metadata' as it's reserved in SQLAlchemy)
    submission_metadata = Column(JSON, nullable=True)  # Browser info, page URL, etc.

