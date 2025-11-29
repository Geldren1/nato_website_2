"""
Base extractor class for opportunity metadata extraction.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from core.logging import get_logger

logger = get_logger(__name__)


class BaseExtractor(ABC):
    """Base class for opportunity metadata extractors."""
    
    def __init__(self, use_llm: bool = True, llm_client=None):
        """
        Initialize extractor.
        
        Args:
            use_llm: Whether to use LLM for extraction
            llm_client: LLM client instance (optional)
        """
        self.use_llm = use_llm
        self.llm_client = llm_client
    
    @abstractmethod
    def extract(self, pdf_text: str, page_info: Dict) -> Dict:
        """
        Extract metadata from PDF text and page info.
        
        Args:
            pdf_text: Extracted text from PDF
            page_info: Basic info from HTML page (url, pdf_url, page_title, etc.)
            
        Returns:
            Dictionary with extracted opportunity data
        """
        pass

