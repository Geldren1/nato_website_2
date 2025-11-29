"""
Application configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List, Union
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/nato_opportunities"
    
    # API Keys
    groq_api_key: Optional[str] = None
    
    # Brevo Email Service (for future use)
    brevo_api_key: Optional[str] = None
    brevo_list_id: Optional[int] = None
    
    # App Configuration
    environment: str = "development"  # development, production, testing
    debug: bool = False
    
    # CORS (comma-separated string in .env)
    allowed_origins: str = "http://localhost:3000,http://localhost:3001"
    allowed_origin_regex: str = r"https://.*\.vercel\.app$"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse allowed_origins from comma-separated string to list."""
        return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]
    
    # Scraper Configuration
    scraper_schedule: str = "daily"
    act_ifib_url: str = "https://www.act.nato.int/act-ifib"
    
    @field_validator('brevo_list_id', mode='before')
    @classmethod
    def parse_brevo_list_id(cls, v: Union[str, int, None]) -> Optional[int]:
        """
        Parse brevo_list_id from string to int.
        
        Handles placeholder strings like 'your_brevo_list_id_here' by returning None.
        """
        if v is None:
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # If it's a placeholder string, return None
            if 'your_' in v.lower() or v.strip() == '':
                return None
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        return None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields (like NEXT_PUBLIC_BACKEND_URL from frontend)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()

