"""
Opportunity database model.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from datetime import datetime
from database.connection import Base


class Opportunity(Base):
    __tablename__ = "opportunities"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core Identification (from scraper)
    opportunity_code = Column(String, unique=True, nullable=False, index=True)
    opportunity_type = Column(String, nullable=True, index=True)  # RFP, RFI, IFIB, NOI, etc.
    nato_body = Column(String, nullable=True, index=True)  # ACT, NCIA, DIANA, etc.
    opportunity_name = Column(String, nullable=False)
    url = Column(String, nullable=False)  # Removed unique constraint to allow amendments with different URLs
    pdf_url = Column(String, nullable=True)
    source_url = Column(String, nullable=True)  # Base URL of the website being scraped
    
    # Contract Details
    contract_type = Column(String, nullable=True)
    document_classification = Column(String, nullable=True)
    response_classification = Column(String, nullable=True)
    contract_duration = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    eligible_organization_types = Column(Text, nullable=True)  # Which types of organizations are eligible to apply
    
    # Important Dates (original strings from PDF)
    clarification_deadline = Column(String, nullable=True)  # Original string from PDF
    clarification_instructions = Column(Text, nullable=True)  # Instructions for bidder clarification
    bid_closing_date = Column(String, nullable=True)  # Original string from PDF
    expected_contract_award_date = Column(String, nullable=True)  # Original string from PDF
    bid_validity_days = Column(Integer, nullable=True)
    
    # Important Dates (parsed to DateTime)
    clarification_deadline_parsed = Column(DateTime, nullable=True, index=True)  # Parsed date
    bid_closing_date_parsed = Column(DateTime, nullable=True, index=True)  # Parsed date
    expected_contract_award_date_parsed = Column(DateTime, nullable=True)  # Parsed date
    
    # Submission Details
    required_documents = Column(Text, nullable=True)  # Text for longer content
    proposal_content = Column(Text, nullable=True)  # What needs to be submitted (e.g., technical and price proposal)
    submission_instructions = Column(Text, nullable=True)
    evaluation_criteria = Column(String, nullable=True)  # Summary of evaluation criteria (e.g., "70/30 technical to price")
    evaluation_criteria_full = Column(Text, nullable=True)  # Full detailed evaluation criteria
    bid_compliance_criteria = Column(Text, nullable=True)  # Bid compliance criteria
    partial_bidding_allowed = Column(Boolean, nullable=True)  # Whether partial bidding is allowed
    
    # Contact Information
    contact_person = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    
    # Additional
    summary = Column(Text, nullable=True)
    
    # Status & Tracking
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    # Only show opportunities where is_active = True
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, server_default=func.now(), server_onupdate=func.now())
    last_checked_at = Column(DateTime, nullable=True)
    # When the scraper last checked this opportunity
    
    # Date tracking for filtering
    opportunity_posted_date = Column(DateTime, nullable=True, index=True)
    # When the opportunity was posted on the NATO website (from opportunity metadata/PDF)
    # This is used for "new this week" filters, not created_at
    
    extracted_at = Column(DateTime, nullable=True)
    # When we scraped/extracted this opportunity (for debugging and tracking)
    
    # Change Tracking (for detecting document updates)
    content_hash = Column(String, nullable=True, index=True)
    # Hash of ALL fields to detect if document content changed
    last_content_update = Column(DateTime, nullable=True, index=True)
    # When the content (not just metadata) was last updated
    update_count = Column(Integer, default=0, nullable=False)
    # Count of how many times this opportunity was updated
    last_changed_fields = Column(JSON, nullable=True)
    # JSON array of field names that changed in the last update (e.g., ["bid_closing_date", "required_documents"])
    
    # Amendment Tracking (for detecting URL changes/amendments)
    amendment_count = Column(Integer, default=0, nullable=False)
    # Count of how many amendments have occurred (URL changes for same opportunity_code)
    has_amendments = Column(Boolean, default=False, nullable=False)
    # Whether any amendments have occurred
    last_amendment_at = Column(DateTime, nullable=True)
    # When the last amendment was detected
    
    # Soft delete tracking
    removed_at = Column(DateTime, nullable=True)
    # When the opportunity was removed from the website (soft delete)
    
    def __repr__(self):
        return f"<Opportunity(id={self.id}, code='{self.opportunity_code}', name='{self.opportunity_name[:50]}...', active={self.is_active})>"

