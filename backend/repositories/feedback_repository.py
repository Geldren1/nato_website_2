"""
Feedback repository for database operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List, Tuple
from models.feedback import Feedback, FeedbackType, FeedbackStatus
from models.roadmap import RoadmapItem, RoadmapCategory, RoadmapStatus


class FeedbackRepository:
    """Repository for feedback database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, feedback_data: dict) -> Feedback:
        """Create a new feedback entry."""
        feedback = Feedback(**feedback_data)
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
    
    def get_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """Get feedback by ID."""
        return self.db.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        feedback_type: Optional[FeedbackType] = None,
        status: Optional[FeedbackStatus] = None,
    ) -> Tuple[List[Feedback], int]:
        """
        Get all feedback with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            feedback_type: Filter by type (bug or improvement)
            status: Filter by status
            
        Returns:
            Tuple of (list of feedback items, total count)
        """
        query = self.db.query(Feedback)
        
        # Apply filters
        if feedback_type:
            query = query.filter(Feedback.type == feedback_type)
        if status:
            query = query.filter(Feedback.status == status)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination and ordering (newest first)
        feedback_items = query.order_by(desc(Feedback.submitted_at)).offset(skip).limit(limit).all()
        
        return feedback_items, total
    
    def get_all_roadmap_items(
        self,
        category: Optional[RoadmapCategory] = None,
        status: Optional[RoadmapStatus] = None,
    ) -> Tuple[List[RoadmapItem], int]:
        """
        Get all roadmap items with optional filtering.
        
        Args:
            category: Filter by category (new_feature or improvement)
            status: Filter by status
            
        Returns:
            Tuple of (list of roadmap items, total count)
        """
        query = self.db.query(RoadmapItem)
        
        # Apply filters
        if category:
            query = query.filter(RoadmapItem.category == category)
        if status:
            query = query.filter(RoadmapItem.status == status)
        
        # Get total count
        total = query.count()
        
        # Order by priority (lower = higher priority), then target_date (most recent first), then created_at (oldest first)
        roadmap_items = query.order_by(
            RoadmapItem.priority.asc().nullslast(),
            desc(RoadmapItem.target_date).nullslast(),
            RoadmapItem.created_at.asc()
        ).all()
        
        return roadmap_items, total

