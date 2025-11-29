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
        exclude_past_due: bool = False
    ) -> Tuple[List[Opportunity], int]:
        """
        Get all opportunities with pagination.
        
        Args:
            is_active: Filter by active status
            skip: Number of records to skip
            limit: Maximum number of records to return
            exclude_past_due: If True, exclude opportunities more than 1 day past closing date
        """
        from datetime import datetime, timedelta
        
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

