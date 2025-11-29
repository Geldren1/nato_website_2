"""
Opportunity repository for database operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List, Tuple
from models.opportunity import Opportunity


class OpportunityRepository:
    """Repository for opportunity database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, opportunity_id: int) -> Optional[Opportunity]:
        """Get opportunity by ID."""
        return self.db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    
    def get_all(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
        exclude_past_due: bool = False,
        opportunity_type: List[str] = None,
        nato_body: List[str] = None,
        search: Optional[str] = None,
        closing_in_7_days: Optional[bool] = None,
        new_this_week: Optional[bool] = None,
        updated_this_week: Optional[bool] = None,
        sort_by: str = "closing_date_asc"
    ) -> Tuple[List[Opportunity], int]:
        """
        Get all opportunities with pagination, filtering, and sorting.
        
        Args:
            is_active: Filter by active status
            skip: Number of records to skip
            limit: Maximum number of records to return
            exclude_past_due: If True, exclude opportunities more than 1 day past closing date
            opportunity_type: List of opportunity types to filter by
            nato_body: List of NATO bodies to filter by
            search: Search term for opportunity name and code
            closing_in_7_days: Filter opportunities closing in next 7 days
            new_this_week: Filter opportunities created this week
            updated_this_week: Filter opportunities updated this week
            sort_by: Sort order
        """
        from datetime import datetime, timedelta
        
        if opportunity_type is None:
            opportunity_type = []
        if nato_body is None:
            nato_body = []
        
        query = self.db.query(Opportunity)
        
        if is_active is not None:
            query = query.filter(Opportunity.is_active == is_active)
        
        # Filter out past-due opportunities (more than 1 day after closing date)
        if exclude_past_due:
            now = datetime.utcnow()
            cutoff_date = now - timedelta(days=1)
            # Include opportunities where:
            # - bid_closing_date_parsed is None (no closing date, so not past due)
            # - OR bid_closing_date_parsed >= cutoff_date (not past due)
            query = query.filter(
                or_(
                    Opportunity.bid_closing_date_parsed.is_(None),
                    Opportunity.bid_closing_date_parsed >= cutoff_date
                )
            )
        
        # Filter by opportunity type
        if opportunity_type:
            query = query.filter(Opportunity.opportunity_type.in_(opportunity_type))
        
        # Filter by NATO body
        if nato_body:
            query = query.filter(Opportunity.nato_body.in_(nato_body))
        
        # Search filter (opportunity name or code)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Opportunity.opportunity_name.ilike(search_term),
                    Opportunity.opportunity_code.ilike(search_term)
                )
            )
        
        # Quick filter: Closing in next 7 days
        if closing_in_7_days:
            now = datetime.utcnow()
            seven_days_later = now + timedelta(days=7)
            query = query.filter(
                and_(
                    Opportunity.bid_closing_date_parsed.isnot(None),
                    Opportunity.bid_closing_date_parsed >= now,
                    Opportunity.bid_closing_date_parsed <= seven_days_later
                )
            )
        
        # Quick filter: New this week
        if new_this_week:
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            query = query.filter(Opportunity.created_at >= week_ago)
        
        # Quick filter: Amended this week (only opportunities with amendments)
        if updated_this_week:
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            # Only show opportunities that have amendments and were amended in the last week
            query = query.filter(
                and_(
                    Opportunity.has_amendments == True,
                    Opportunity.last_amendment_at.isnot(None),
                    Opportunity.last_amendment_at >= week_ago
                )
            )
        
        # Sorting
        if sort_by == "closing_date_asc":
            query = query.order_by(Opportunity.bid_closing_date_parsed.asc().nulls_last())
        elif sort_by == "closing_date_desc":
            query = query.order_by(Opportunity.bid_closing_date_parsed.desc().nulls_last())
        elif sort_by == "recently_updated":
            query = query.order_by(Opportunity.updated_at.desc())
        elif sort_by == "recently_added":
            query = query.order_by(Opportunity.created_at.desc())
        elif sort_by == "name_asc":
            query = query.order_by(Opportunity.opportunity_name.asc())
        else:
            # Default: closing_date_asc
            query = query.order_by(Opportunity.bid_closing_date_parsed.asc().nulls_last())
        
        total = query.count()
        opportunities = query.offset(skip).limit(limit).all()
        
        return opportunities, total
    
    def get_by_code(self, opportunity_code: str) -> Optional[Opportunity]:
        """Get opportunity by code."""
        return self.db.query(Opportunity).filter(Opportunity.opportunity_code == opportunity_code).first()
    
    def create(self, opportunity: Opportunity) -> Opportunity:
        """Create a new opportunity."""
        self.db.add(opportunity)
        self.db.commit()
        self.db.refresh(opportunity)
        return opportunity
    
    def update(self, opportunity: Opportunity) -> Opportunity:
        """Update an existing opportunity."""
        self.db.commit()
        self.db.refresh(opportunity)
        return opportunity
    
    def delete(self, opportunity: Opportunity) -> None:
        """Delete an opportunity."""
        self.db.delete(opportunity)
        self.db.commit()

