"""
Opportunities API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from services.opportunity_service import OpportunityService
from schemas.opportunity import OpportunityResponse, OpportunityListResponse
from app.dependencies import get_opportunity_service
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("", response_model=OpportunityListResponse)
async def get_opportunities(
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    service: OpportunityService = Depends(get_opportunity_service)
):
    """
    Get list of opportunities with pagination.
    
    By default, returns only active opportunities.
    
    Args:
        is_active: Filter by active status (default: True)
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 100)
        service: Opportunity service (injected)
        
    Returns:
        List of opportunities with pagination info
    """
    try:
        return service.get_opportunities(
            is_active=is_active,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error fetching opportunities: {str(e)}", event_type="api_error")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: int,
    service: OpportunityService = Depends(get_opportunity_service)
):
    """
    Get a single opportunity by ID.
    
    Args:
        opportunity_id: Opportunity ID
        service: Opportunity service (injected)
        
    Returns:
        Opportunity details
    """
    try:
        opportunity = service.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return opportunity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching opportunity {opportunity_id}: {str(e)}", event_type="api_error")
        raise HTTPException(status_code=500, detail="Internal server error")

