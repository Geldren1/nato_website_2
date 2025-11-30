"""
Custom exceptions for the application.
"""


class NATOOpportunitiesException(Exception):
    """Base exception for all application exceptions."""
    pass


class OpportunityNotFoundError(NATOOpportunitiesException):
    """Raised when an opportunity is not found."""
    pass


class ValidationError(NATOOpportunitiesException):
    """Raised when validation fails."""
    pass


class DatabaseError(NATOOpportunitiesException):
    """Raised when a database operation fails."""
    pass


class ExternalServiceError(NATOOpportunitiesException):
    """Raised when an external service call fails."""
    pass


class BrevoError(ExternalServiceError):
    """Raised when Brevo API operations fail."""
    pass


class ScraperError(NATOOpportunitiesException):
    """Raised when scraper operations fail."""
    pass


class ConfigurationError(NATOOpportunitiesException):
    """Raised when configuration is invalid or missing."""
    pass

