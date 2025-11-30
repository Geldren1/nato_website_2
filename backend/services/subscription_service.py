"""
Service for email subscription business logic.
Manages subscriptions solely through Brevo - no local database storage.
"""

from typing import Optional, Dict, Any
from external.brevo.client import get_brevo_client
from core.exceptions import ValidationError
from core.logging import get_logger

logger = get_logger(__name__)


class SubscriptionService:
    """Service for email subscription business logic (Brevo-only)."""
    
    def __init__(self):
        self.brevo_client = get_brevo_client()
    
    def subscribe(self, email: str, preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Subscribe an email address via Brevo.
        
        Args:
            email: Email address
            preferences: Optional subscription preferences
            
        Returns:
            Dictionary with subscription result
        """
        email = email.lower().strip()
        
        if not email or '@' not in email:
            raise ValidationError("Invalid email address")
        
        if not self.brevo_client.is_configured():
            logger.warning("Brevo not configured, cannot subscribe")
            return {
                "success": False,
                "message": "Email service not configured",
                "email": email
            }
        
        try:
            brevo_id = self.brevo_client.add_contact(email, preferences)
            
            if brevo_id:
                logger.info(f"Subscribed {email} via Brevo")
                return {
                    "success": True,
                    "message": "Successfully subscribed to opportunity alerts",
                    "email": email
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to subscribe",
                    "email": email
                }
        except Exception as e:
            logger.error(f"Error subscribing {email}: {e}")
            return {
                "success": False,
                "message": f"Error subscribing: {str(e)}",
                "email": email
            }
    
    def unsubscribe(self, email: str) -> Dict[str, Any]:
        """
        Unsubscribe an email address via Brevo.
        
        Args:
            email: Email address
            
        Returns:
            Dictionary with unsubscribe result
        """
        email = email.lower().strip()
        
        if not email or '@' not in email:
            raise ValidationError("Invalid email address")
        
        if not self.brevo_client.is_configured():
            logger.warning("Brevo not configured, cannot unsubscribe")
            return {
                "success": False,
                "message": "Email service not configured",
                "email": email
            }
        
        try:
            success = self.brevo_client.remove_contact(email)
            
            if success:
                logger.info(f"Unsubscribed {email} via Brevo")
                return {
                    "success": True,
                    "message": "Successfully unsubscribed from opportunity alerts",
                    "email": email
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to unsubscribe",
                    "email": email
                }
        except Exception as e:
            logger.error(f"Error unsubscribing {email}: {e}")
            return {
                "success": False,
                "message": f"Error unsubscribing: {str(e)}",
                "email": email
            }
    
    def get_subscribers(self, limit: int = 100) -> list:
        """
        Get list of subscriber emails from Brevo.
        
        Args:
            limit: Maximum number of emails to return
            
        Returns:
            List of email addresses
        """
        if not self.brevo_client.is_configured():
            logger.warning("Brevo not configured, cannot fetch subscribers")
            return []
        
        return self.brevo_client.get_contacts_from_list(limit=limit)

