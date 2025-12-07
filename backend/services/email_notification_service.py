"""
Email notification service for opportunity updates.
Integrates with the daily scraper job to send notifications.
"""

from typing import List, Dict, Any
from models import Opportunity
from external.email.sender import get_email_sender
from external.brevo.client import get_brevo_client
from core.logging import get_logger

logger = get_logger(__name__)


class EmailNotificationService:
    """Service for sending email notifications about opportunity changes."""
    
    def __init__(self):
        self.email_sender = get_email_sender()
        self.brevo_client = get_brevo_client()
    
    def send_notifications_for_changes(
        self,
        new_opportunities: List[Opportunity],
        amended_opportunities: List[Opportunity]
    ) -> Dict[str, Any]:
        """
        Send email notifications for new and amended opportunities.
        
        Args:
            new_opportunities: List of newly created opportunities
            amended_opportunities: List of amended opportunities
            
        Returns:
            Dictionary with notification results
        """
        if not self.email_sender.is_configured():
            logger.warning("Email service not configured, skipping notifications")
            return {
                "new_sent": 0,
                "new_failed": 0,
                "amended_sent": 0,
                "amended_failed": 0,
                "errors": ["Email service not configured"]
            }
        
        # Get subscriber emails from Brevo (max limit is 500)
        subscriber_emails = self.brevo_client.get_contacts_from_list(limit=500)
        
        if not subscriber_emails:
            logger.info("No subscribers found, skipping email notifications")
            return {
                "new_sent": 0,
                "new_failed": 0,
                "amended_sent": 0,
                "amended_failed": 0,
                "subscriber_count": 0
            }
        
        logger.info(f"Found {len(subscriber_emails)} subscribers, sending summary email...")
        
        results = {
            "sent": 0,
            "failed": 0,
            "subscriber_count": len(subscriber_emails),
            "new_count": len(new_opportunities),
            "amended_count": len(amended_opportunities),
            "errors": []
        }
        
        # Send single summary email with all changes
        try:
            email_results = self.email_sender.send_daily_summary_notification(
                new_opportunities=new_opportunities,
                amended_opportunities=amended_opportunities,
                subscriber_emails=subscriber_emails
            )
            results["sent"] = email_results.get("sent", 0)
            results["failed"] = email_results.get("failed", 0)
            if email_results.get("errors"):
                results["errors"].extend(email_results["errors"])
            
            logger.info(
                f"Sent summary email: {results['sent']} sent, {results['failed']} failed | "
                f"({len(new_opportunities)} new, {len(amended_opportunities)} amended)"
            )
        except Exception as e:
            error_msg = f"Error sending summary email: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["failed"] = len(subscriber_emails)
        
        logger.info(
            f"Email notifications complete: "
            f"{results['sent']} summary emails sent, {results['failed']} failed"
        )
        
        return results


def get_email_notification_service() -> EmailNotificationService:
    """Get email notification service instance."""
    return EmailNotificationService()

