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
        limit: int = 50
    ) -> Tuple[List[Opportunity], int]:
        """Get all opportunities with pagination."""
        query = self.db.query(Opportunity)
        
        if is_active is not None:
            query = query.filter(Opportunity.is_active == is_active)
        
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

