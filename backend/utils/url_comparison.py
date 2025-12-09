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


def extract_pdf_filename(pdf_url: str) -> Optional[str]:
    """
    Extract the filename from a PDF URL.
    
    Examples:
    - https://www.act.nato.int/wp-content/uploads/2025/11/ifib026007.pdf
      → ifib026007.pdf
    - https://www.act.nato.int/wp-content/uploads/2025/11/ifib026007_amdt1.pdf
      → ifib026007_amdt1.pdf
    
    Args:
        pdf_url: The PDF URL
        
    Returns:
        The filename (last segment of path), or None if URL is invalid
    """
    if not pdf_url:
        return None
    
    try:
        parsed = urlparse(pdf_url)
        path = parsed.path
        
        # Get the last segment (filename)
        segments = path.split('/')
        filename = segments[-1] if segments else None
        
        logger.debug(f"Extracted PDF filename '{filename}' from '{pdf_url}'")
        return filename
        
    except Exception as e:
        logger.warning(f"Error extracting PDF filename from '{pdf_url}': {e}")
        return None


def pdf_urls_differ(pdf_url1: Optional[str], pdf_url2: Optional[str]) -> bool:
    """
    Compare PDF URLs by their filenames to detect if PDF has changed (amendment).
    
    This function extracts the filename from each PDF URL and compares them.
    If the filenames differ, it indicates the PDF has changed (e.g., an amendment).
    
    Examples:
    - ifib026007.pdf vs ifib026007_amdt1.pdf → True (different, amendment)
    - ifib026007.pdf vs ifib026007.pdf → False (same)
    - ifib026007.pdf vs None → True (one missing)
    
    Args:
        pdf_url1: First PDF URL to compare
        pdf_url2: Second PDF URL to compare
        
    Returns:
        True if PDF filenames differ, False if they are the same
    """
    if not pdf_url1 or not pdf_url2:
        # If either is missing, consider them different
        if pdf_url1 != pdf_url2:
            logger.debug(f"One PDF URL is missing: pdf_url1='{pdf_url1}', pdf_url2='{pdf_url2}'")
            return True
        return False
    
    filename1 = extract_pdf_filename(pdf_url1)
    filename2 = extract_pdf_filename(pdf_url2)
    
    # If either filename extraction failed, fall back to full URL comparison
    if filename1 is None or filename2 is None:
        logger.debug(f"Could not extract filenames, comparing full PDF URLs: '{pdf_url1}' vs '{pdf_url2}'")
        return pdf_url1 != pdf_url2
    
    # Compare the filenames (case-insensitive)
    differ = filename1.lower() != filename2.lower()
    
    if differ:
        logger.info(f"PDF filenames differ: '{filename1}' vs '{filename2}' (potential amendment)")
    else:
        logger.debug(f"PDF filenames match: '{filename1}' == '{filename2}'")
    
    return differ


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

