"""
Structured logging configuration.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime


class StructuredLogger:
    """Logger that supports structured logging with context."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log_with_context(
        self,
        level: int,
        message: str,
        event_type: Optional[str] = None,
        **context: Any
    ):
        """Log with structured context."""
        extra = {
            "event_type": event_type or "general",
            "timestamp": datetime.utcnow().isoformat(),
            **context
        }
        self.logger.log(level, message, extra=extra)
    
    def info(self, message: str, event_type: Optional[str] = None, **context: Any):
        """Log info level message with context."""
        self._log_with_context(logging.INFO, message, event_type, **context)
    
    def error(self, message: str, event_type: Optional[str] = None, **context: Any):
        """Log error level message with context."""
        self._log_with_context(logging.ERROR, message, event_type, **context)
    
    def warning(self, message: str, event_type: Optional[str] = None, **context: Any):
        """Log warning level message with context."""
        self._log_with_context(logging.WARNING, message, event_type, **context)
    
    def debug(self, message: str, event_type: Optional[str] = None, **context: Any):
        """Log debug level message with context."""
        self._log_with_context(logging.DEBUG, message, event_type, **context)
    
    # Convenience methods for common events
    def log_opportunity_fetched(
        self,
        count: int,
        filters: Optional[Dict[str, Any]] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ):
        """Log opportunity fetch event."""
        self.info(
            f"Fetched {count} opportunities",
            event_type="opportunity_fetch",
            count=count,
            filters=filters or {},
            page=page,
            page_size=page_size
        )
    
    def log_opportunity_created(self, opportunity_id: int, opportunity_code: str):
        """Log opportunity creation event."""
        self.info(
            f"Created opportunity {opportunity_code}",
            event_type="opportunity_created",
            opportunity_id=opportunity_id,
            opportunity_code=opportunity_code
        )
    
    def log_opportunity_updated(
        self,
        opportunity_id: int,
        opportunity_code: str,
        changed_fields: Optional[list] = None
    ):
        """Log opportunity update event."""
        self.info(
            f"Updated opportunity {opportunity_code}",
            event_type="opportunity_updated",
            opportunity_id=opportunity_id,
            opportunity_code=opportunity_code,
            changed_fields=changed_fields or []
        )
    
    def log_scraper_run(
        self,
        config_name: str,
        opportunities_found: int,
        opportunities_created: int,
        opportunities_updated: int
    ):
        """Log scraper run event."""
        self.info(
            f"Scraper run completed for {config_name}",
            event_type="scraper_run",
            config_name=config_name,
            opportunities_found=opportunities_found,
            opportunities_created=opportunities_created,
            opportunities_updated=opportunities_updated
        )


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)

