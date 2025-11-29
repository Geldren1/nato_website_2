"""
Opportunity service for business logic.
"""

from typing import Optional
from repositories.opportunity_repository import OpportunityRepository
from schemas.opportunity import OpportunityResponse, OpportunityListResponse
from models.opportunity import Opportunity


class OpportunityService:
    """Service for opportunity business logic."""
    
    def __init__(self, repository: OpportunityRepository):
        self.repository = repository
    
    def get_opportunities(
        self,
        is_active: Optional[bool] = True,
        page: int = 1,
        page_size: int = 50
    ) -> OpportunityListResponse:
        """
        Get paginated list of opportunities.
        
        When is_active=True, automatically filters out opportunities that are
        more than 1 day past their closing date.
        """
        skip = (page - 1) * page_size
        
        # When is_active=True, exclude past-due opportunities (more than 1 day after closing)
        exclude_past_due = is_active is True
        
        opportunities, total = self.repository.get_all(
            is_active=is_active,
            skip=skip,
            limit=page_size,
            exclude_past_due=exclude_past_due
        )
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return OpportunityListResponse(
            items=[OpportunityResponse.model_validate(opp) for opp in opportunities],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def get_opportunity_by_id(self, opportunity_id: int) -> Optional[OpportunityResponse]:
        """Get opportunity by ID."""
        opportunity = self.repository.get_by_id(opportunity_id)
        if not opportunity:
            return None
        return OpportunityResponse.model_validate(opportunity)

