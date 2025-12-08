"""
Feedback API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from database.connection import get_db
from repositories.feedback_repository import FeedbackRepository
from schemas.feedback import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackListResponse,
    RoadmapItemResponse,
    RoadmapListResponse
)
from models.feedback import FeedbackType, FeedbackStatus
from models.roadmap import RoadmapCategory, RoadmapStatus
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_feedback_repository(db: Session = Depends(get_db)) -> FeedbackRepository:
    """Dependency to get feedback repository."""
    return FeedbackRepository(db)


@router.post("", response_model=FeedbackResponse, status_code=201)
async def create_feedback(
    feedback: FeedbackCreate,
    repository: FeedbackRepository = Depends(get_feedback_repository)
):
    """
    Submit new feedback (bug report or improvement suggestion).
    
    Public endpoint - no authentication required.
    
    Args:
        feedback: Feedback submission data
        repository: Feedback repository (injected)
        
    Returns:
        Created feedback item
    """
    try:
        feedback_data = feedback.model_dump()
        # Ensure status is set to OPEN for new submissions
        feedback_data['status'] = FeedbackStatus.OPEN
        
        created_feedback = repository.create(feedback_data)
        logger.info(f"New feedback submitted: {created_feedback.id} - {created_feedback.type.value} - {created_feedback.title}")
        
        return created_feedback
    except Exception as e:
        logger.error(f"Error creating feedback: {str(e)}", event_type="api_error")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=FeedbackListResponse)
async def get_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    type: Optional[str] = Query(None, description="Filter by type: bug or improvement"),
    status: Optional[str] = Query(None, description="Filter by status: open, in_progress, resolved, rejected"),
    repository: FeedbackRepository = Depends(get_feedback_repository)
):
    """
    Get list of feedback with pagination and filtering.
    
    Public endpoint - returns all feedback (excluding admin_notes).
    
    Args:
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 100)
        type: Filter by type (bug or improvement)
        status: Filter by status
        repository: Feedback repository (injected)
        
    Returns:
        List of feedback items with pagination info
    """
    try:
        skip = (page - 1) * page_size
        
        # Parse enum filters
        feedback_type = None
        if type:
            try:
                feedback_type = FeedbackType(type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid type: {type}. Must be 'bug' or 'improvement'")
        
        feedback_status = None
        if status:
            try:
                feedback_status = FeedbackStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}. Must be 'open', 'in_progress', 'resolved', or 'rejected'")
        
        feedback_items, total = repository.get_all(
            skip=skip,
            limit=page_size,
            feedback_type=feedback_type,
            status=feedback_status
        )
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return FeedbackListResponse(
            items=feedback_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching feedback: {str(e)}", event_type="api_error")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/roadmap", response_model=RoadmapListResponse)
async def get_roadmap(
    category: Optional[str] = Query(None, description="Filter by category: new_feature or improvement"),
    status: Optional[str] = Query(None, description="Filter by status: planned, in_progress, completed, cancelled"),
    repository: FeedbackRepository = Depends(get_feedback_repository)
):
    """
    Get roadmap items.
    
    Public endpoint - returns all roadmap items.
    
    Args:
        category: Filter by category (new_feature or improvement)
        status: Filter by status
        repository: Feedback repository (injected)
        
    Returns:
        List of roadmap items
    """
    try:
        # Parse enum filters
        roadmap_category = None
        if category:
            try:
                roadmap_category = RoadmapCategory(category.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}. Must be 'new_feature' or 'improvement'")
        
        roadmap_status = None
        if status:
            try:
                roadmap_status = RoadmapStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}. Must be 'planned', 'in_progress', 'completed', or 'cancelled'")
        
        roadmap_items, total = repository.get_all_roadmap_items(
            category=roadmap_category,
            status=roadmap_status
        )
        
        return RoadmapListResponse(
            items=roadmap_items,
            total=total
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching roadmap: {str(e)}", event_type="api_error")
        raise HTTPException(status_code=500, detail="Internal server error")

