"""
Extractors for different opportunity types.
"""

from scraper.extractors.base import BaseExtractor
from typing import Optional


def get_act_extractor(opportunity_type: Optional[str], use_llm: bool = True, llm_client=None) -> BaseExtractor:
    """
    Get the appropriate ACT extractor for an opportunity type.
    
    Args:
        opportunity_type: The opportunity type (IFIB, NOI, RFP, RFI, etc.)
        use_llm: Whether to use LLM for extraction
        llm_client: LLM client instance (optional)
        
    Returns:
        BaseExtractor instance
    """
    if not opportunity_type:
        raise ValueError("opportunity_type is required")
    
    opportunity_type_upper = opportunity_type.upper()
    
    if opportunity_type_upper == "IFIB":
        from scraper.extractors.act_ifib_extractor import ACTIFIBExtractor
        return ACTIFIBExtractor(use_llm=use_llm, llm_client=llm_client)
    elif opportunity_type_upper == "NOI":
        from scraper.extractors.act_noi_extractor import ACTNOIExtractor
        return ACTNOIExtractor(use_llm=use_llm, llm_client=llm_client)
    
    # For other types, we can add extractors later
    raise NotImplementedError(f"ACT extractor for opportunity type '{opportunity_type}' not yet implemented")

