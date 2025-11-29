"""
Opportunity Pydantic schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class OpportunityBase(BaseModel):
    """Base opportunity schema."""
    opportunity_code: str
    opportunity_type: Optional[str] = None
    nato_body: Optional[str] = None
    opportunity_name: str
    url: str
    pdf_url: Optional[str] = None
    source_url: Optional[str] = None


class OpportunityResponse(OpportunityBase):
    """Opportunity response schema."""
    id: int
    contract_type: Optional[str] = None
    document_classification: Optional[str] = None
    response_classification: Optional[str] = None
    contract_duration: Optional[str] = None
    currency: Optional[str] = None
    eligible_organization_types: Optional[str] = None
    clarification_deadline: Optional[str] = None
    clarification_instructions: Optional[str] = None
    bid_closing_date: Optional[str] = None
    expected_contract_award_date: Optional[str] = None
    bid_validity_days: Optional[int] = None
    clarification_deadline_parsed: Optional[datetime] = None
    bid_closing_date_parsed: Optional[datetime] = None
    expected_contract_award_date_parsed: Optional[datetime] = None
    required_documents: Optional[str] = None
    proposal_content: Optional[str] = None
    submission_instructions: Optional[str] = None
    evaluation_criteria: Optional[str] = None
    evaluation_criteria_full: Optional[str] = None
    bid_compliance_criteria: Optional[str] = None
    partial_bidding_allowed: Optional[bool] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    summary: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_checked_at: Optional[datetime] = None
    opportunity_posted_date: Optional[datetime] = None
    extracted_at: Optional[datetime] = None
    content_hash: Optional[str] = None
    last_content_update: Optional[datetime] = None
    update_count: int
    last_changed_fields: Optional[List[str]] = None
    amendment_count: int
    has_amendments: bool
    last_amendment_at: Optional[datetime] = None
    removed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OpportunityListResponse(BaseModel):
    """Opportunity list response with pagination."""
    items: List[OpportunityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

