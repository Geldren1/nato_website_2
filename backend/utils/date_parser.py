"""
Date parsing utilities for opportunity dates.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional
from dateutil import parser as date_parser
from core.logging import get_logger

logger = get_logger(__name__)


def parse_date_string(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse a date string into a datetime object.
    
    Handles various formats:
    - "15 November 2025"
    - "15 Nov 2025"
    - "2025-11-15"
    - "15/11/2025"
    - "November 15, 2025"
    - Dates with time: "15 November 2025 at 14:00 CET"
    
    Args:
        date_str: Date string to parse
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    # Clean up the string
    date_str = date_str.strip()
    
    # Try to extract timezone information
    timezone_patterns = [
        r'\b(CET|CEST|UTC|GMT|EST|EDT|PST|PDT)\b',
        r'\b([A-Z]{3,4})\b',  # General timezone abbreviations
    ]
    
    timezone = None
    for pattern in timezone_patterns:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            timezone = match.group(1)
            break
    
    # Remove timezone from string for parsing
    date_str_clean = re.sub(r'\b(CET|CEST|UTC|GMT|EST|EDT|PST|PDT)\b', '', date_str, flags=re.IGNORECASE)
    date_str_clean = re.sub(r'\s+', ' ', date_str_clean).strip()
    
    # Try to extract time if present
    time_match = re.search(r'(\d{1,2}):(\d{2})', date_str_clean)
    time_hour = None
    time_minute = None
    if time_match:
        time_hour = int(time_match.group(1))
        time_minute = int(time_match.group(2))
        # Remove time from string
        date_str_clean = re.sub(r'\d{1,2}:\d{2}', '', date_str_clean).strip()
        date_str_clean = re.sub(r'\s+at\s+', ' ', date_str_clean, flags=re.IGNORECASE)
    
    try:
        # Try dateutil parser first (most flexible)
        parsed_date = date_parser.parse(date_str_clean, fuzzy=True, default=datetime.now())
        
        # Apply time if found
        if time_hour is not None and time_minute is not None:
            parsed_date = parsed_date.replace(hour=time_hour, minute=time_minute, second=0, microsecond=0)
        
        return parsed_date
    except Exception as e:
        logger.debug(f"Failed to parse date '{date_str}': {e}")
        return None


def parse_opportunity_dates(opportunity_data: Dict) -> Dict:
    """
    Parse date strings in opportunity data to datetime objects.
    
    Args:
        opportunity_data: Dictionary with opportunity data containing date strings
        
    Returns:
        Dictionary with parsed dates added (with _parsed suffix)
    """
    # Parse clarification deadline
    if opportunity_data.get('clarification_deadline'):
        parsed = parse_date_string(opportunity_data['clarification_deadline'])
        if parsed:
            opportunity_data['clarification_deadline_parsed'] = parsed
    
    # Parse bid closing date
    if opportunity_data.get('bid_closing_date'):
        parsed = parse_date_string(opportunity_data['bid_closing_date'])
        if parsed:
            opportunity_data['bid_closing_date_parsed'] = parsed
    
    # Parse expected contract award date
    if opportunity_data.get('expected_contract_award_date'):
        parsed = parse_date_string(opportunity_data['expected_contract_award_date'])
        if parsed:
            opportunity_data['expected_contract_award_date_parsed'] = parsed
    
    # Parse target issue date (for NOI)
    if opportunity_data.get('target_issue_date'):
        parsed = parse_date_string(opportunity_data['target_issue_date'])
        if parsed:
            opportunity_data['target_issue_date_parsed'] = parsed
    
    # Parse target bid closing date (for NOI)
    if opportunity_data.get('target_bid_closing_date'):
        parsed = parse_date_string(opportunity_data['target_bid_closing_date'])
        if parsed:
            opportunity_data['target_bid_closing_date_parsed'] = parsed
    
    return opportunity_data

