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
    opportunity_type: Optional[List[str]] = Query(None, description="Filter by opportunity types"),
    nato_body: Optional[List[str]] = Query(None, description="Filter by NATO bodies"),
    search: Optional[str] = Query(None, description="Search in opportunity name and code"),
    closing_in_7_days: Optional[bool] = Query(None, description="Filter opportunities closing in next 7 days"),
    new_this_week: Optional[bool] = Query(None, description="Filter opportunities created this week"),
    updated_this_week: Optional[bool] = Query(None, description="Filter opportunities updated this week"),
    sort_by: Optional[str] = Query("closing_date_asc", description="Sort order"),
    service: OpportunityService = Depends(get_opportunity_service)
):
    """
    Get list of opportunities with pagination and filtering.
    
    By default, returns only active opportunities.
    
    Args:
        is_active: Filter by active status (default: True)
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 100)
        opportunity_type: Filter by opportunity types (e.g., IFIB, RFP)
        nato_body: Filter by NATO bodies (e.g., ACT, NCIA)
        search: Search in opportunity name and code
        closing_in_7_days: Filter opportunities closing in next 7 days
        new_this_week: Filter opportunities created this week
        updated_this_week: Filter opportunities updated this week
        sort_by: Sort order (closing_date_asc, closing_date_desc, recently_updated, recently_added, name_asc)
        service: Opportunity service (injected)
        
    Returns:
        List of opportunities with pagination info
    """
    try:
        return service.get_opportunities(
            is_active=is_active,
            page=page,
            page_size=page_size,
            opportunity_type=opportunity_type or [],
            nato_body=nato_body or [],
            search=search,
            closing_in_7_days=closing_in_7_days,
            new_this_week=new_this_week,
            updated_this_week=updated_this_week,
            sort_by=sort_by
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

