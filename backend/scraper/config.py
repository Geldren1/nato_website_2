"""
Scraper configuration for ACT scrapers.
"""

SCRAPER_CONFIGS = {
    "ACT": {
        "enabled": True,
        "nato_body": "ACT",
        "base_url": "https://www.act.nato.int/opportunities/contracting/",
        "opportunity_list_url": "https://www.act.nato.int/opportunities/contracting/",
        "url_pattern": r"https://www\.act\.nato\.int/opportunities/contracting/[^/?#]+/?$",
        "pdf_selector": 'a[target="_blank"][rel="noopener"]',
        "scraper_type": "link_based",
    },
}


def extract_nato_body_from_url(url: str, config: dict) -> str:
    """
    Extract NATO body from URL/domain or config.
    
    Args:
        url: The opportunity URL
        config: Scraper configuration dict
        
    Returns:
        NATO body string
    """
    # Extract from config (preferred)
    if config and "nato_body" in config:
        return config["nato_body"]
    
    # Fallback: extract from URL
    if "act.nato.int" in url.lower():
        return "ACT"
    elif "ncia.nato.int" in url.lower():
        return "NCIA"
    elif "nspa.nato.int" in url.lower() or "eportal.nspa" in url.lower():
        return "NSPA"
    elif "diana.nato.int" in url.lower():
        return "DIANA"
    
    return None

