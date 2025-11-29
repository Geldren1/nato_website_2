"""
FastAPI dependencies for dependency injection.
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from repositories.opportunity_repository import OpportunityRepository
from services.opportunity_service import OpportunityService


def get_opportunity_repository(db: Session = Depends(get_db)) -> OpportunityRepository:
    """
    Dependency to get opportunity repository.
    
    Args:
        db: Database session
        
    Returns:
        Opportunity repository instance
    """
    return OpportunityRepository(db)


def get_opportunity_service(
    repository: OpportunityRepository = Depends(get_opportunity_repository)
) -> OpportunityService:
    """
    Dependency to get opportunity service.
    
    Args:
        repository: Opportunity repository
        
    Returns:
        Opportunity service instance
    """
    return OpportunityService(repository)

