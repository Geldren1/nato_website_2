"""
URL comparison utilities for detecting amendments and URL changes.
"""

from typing import Optional
from urllib.parse import urlparse
from core.logging import get_logger

logger = get_logger(__name__)


def extract_url_ending(url: str) -> Optional[str]:
    """
    Extract the last segment of URL (after last '/').
    
    Examples:
    - https://www.act.nato.int/opportunities/contracting/ifib-act-sact-26-07/
      → ifib-act-sact-26-07
    - https://www.act.nato.int/opportunities/contracting/ifib-act-sact-26-07-amendment-1/
      → ifib-act-sact-26-07-amendment-1
    - https://www.act.nato.int/opportunities/contracting/ifib-act-sact-26-07
      → ifib-act-sact-26-07
    
    Args:
        url: The URL to extract the ending from
        
    Returns:
        The last segment of the URL path, or None if URL is invalid
    """
    if not url:
        return None
    
    try:
        # Parse the URL
        parsed = urlparse(url)
        path = parsed.path
        
        # Remove leading and trailing slashes, then split
        path = path.strip('/')
        if not path:
            return None
        
        # Get the last segment
        segments = path.split('/')
        ending = segments[-1] if segments else None
        
        logger.debug(f"Extracted URL ending '{ending}' from '{url}'")
        return ending
        
    except Exception as e:
        logger.warning(f"Error extracting URL ending from '{url}': {e}")
        return None


def urls_differ_by_ending(url1: str, url2: str) -> bool:
    """
    Compare URL endings to detect if URLs differ (indicating potential amendment).
    
    This function extracts the last segment of each URL and compares them.
    If the endings differ, it indicates the URL has changed (e.g., an amendment).
    
    Examples:
    - ifib-act-sact-26-07/ vs ifib-act-sact-26-07-amendment-1/ → True (different)
    - ifib-act-sact-26-07/ vs ifib-act-sact-26-07/ → False (same)
    - ifib-act-sact-26-07 vs ifib-act-sact-26-07/ → False (same, trailing slash ignored)
    
    Args:
        url1: First URL to compare
        url2: Second URL to compare
        
    Returns:
        True if URL endings differ, False if they are the same
    """
    if not url1 or not url2:
        logger.debug(f"One or both URLs are empty: url1='{url1}', url2='{url2}'")
        return url1 != url2
    
    ending1 = extract_url_ending(url1)
    ending2 = extract_url_ending(url2)
    
    # If either ending extraction failed, fall back to full URL comparison
    if ending1 is None or ending2 is None:
        logger.debug(f"Could not extract endings, comparing full URLs: '{url1}' vs '{url2}'")
        return url1 != url2
    
    # Compare the endings (case-insensitive)
    differ = ending1.lower() != ending2.lower()
    
    if differ:
        logger.info(f"URL endings differ: '{ending1}' vs '{ending2}' (potential amendment)")
    else:
        logger.debug(f"URL endings match: '{ending1}' == '{ending2}'")
    
    return differ

