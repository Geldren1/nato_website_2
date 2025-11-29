"""
Groq API client wrapper.
"""

from typing import Optional
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class GroqClient:
    """Client for Groq API operations."""
    
    def __init__(self):
        """Initialize Groq client."""
        self.api_key = settings.groq_api_key
        self._client = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure Groq client is initialized."""
        if self._initialized:
            return
        
        if not self.api_key:
            logger.warning("Groq API key not configured")
            return
        
        try:
            from groq import Groq
            # Set timeout to 120 seconds (2 minutes) to avoid 1-minute default timeout issues
            # This is especially important for large PDF extractions
            self._client = Groq(api_key=self.api_key, timeout=120.0)
            self._initialized = True
            logger.info("Groq client initialized successfully with 120s timeout")
        except Exception as e:
            logger.warning(f"Could not initialize Groq client: {e}")
            raise Exception(f"Failed to initialize Groq client: {e}")
    
    def is_configured(self) -> bool:
        """
        Check if Groq is configured.
        
        Returns:
            True if configured, False otherwise
        """
        return bool(self.api_key)
    
    def get_client(self):
        """
        Get Groq client instance.
        
        Returns:
            Groq client instance or None if not configured
            
        Raises:
            Exception: If initialization fails
        """
        if not self.is_configured():
            return None
        
        self._ensure_initialized()
        return self._client


def get_groq_client() -> Optional[GroqClient]:
    """
    Get Groq client instance.
    
    Returns:
        GroqClient instance or None if not configured
    """
    if not settings.groq_api_key:
        return None
    return GroqClient()

