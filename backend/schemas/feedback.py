"""
Feedback Pydantic schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.feedback import FeedbackType, FeedbackStatus, FeedbackPriority
from models.roadmap import RoadmapCategory, RoadmapStatus


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""
    type: FeedbackType = Field(..., description="Type of feedback: bug or improvement")
    title: str = Field(..., min_length=1, max_length=200, description="Brief title of the feedback")
    description: str = Field(..., min_length=1, description="Detailed description")
    submitted_by: Optional[str] = Field(None, max_length=255, description="Email or name (optional)")
    priority: Optional[FeedbackPriority] = Field(None, description="Priority level (optional)")
    submission_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata (browser info, page URL, etc.)")


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: int
    type: FeedbackType
    title: str
    description: str
    status: FeedbackStatus
    priority: Optional[FeedbackPriority] = None
    submitted_by: Optional[str] = None
    submitted_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    # Note: admin_notes is excluded from public API
    submission_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    """Schema for paginated feedback list response."""
    items: List[FeedbackResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RoadmapItemResponse(BaseModel):
    """Schema for roadmap item response."""
    id: int
    title: str
    description: Optional[str] = None
    category: RoadmapCategory
    status: RoadmapStatus
    priority: Optional[int] = None
    target_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    related_feedback_ids: Optional[List[int]] = None

    class Config:
        from_attributes = True


class RoadmapListResponse(BaseModel):
    """Schema for roadmap list response."""
    items: List[RoadmapItemResponse]
    total: int

