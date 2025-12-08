"""
Roadmap database model.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from database.connection import Base
import enum


class RoadmapCategory(str, enum.Enum):
    """Roadmap category enumeration."""
    NEW_FEATURE = "new_feature"
    IMPROVEMENT = "improvement"


class RoadmapStatus(str, enum.Enum):
    """Roadmap status enumeration."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core Fields
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(RoadmapCategory), nullable=False, index=True)
    status = Column(SQLEnum(RoadmapStatus), nullable=False, default=RoadmapStatus.PLANNED, index=True)
    priority = Column(Integer, nullable=True, index=True)  # For sorting (lower = higher priority)
    
    # Target Date
    target_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, server_default=func.now(), server_onupdate=func.now())
    
    # Related Feedback
    related_feedback_ids = Column(JSON, nullable=True)  # Array of feedback IDs that led to this roadmap item

