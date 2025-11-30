"""
Email sender for opportunity notifications.
Uses Brevo (Sendinblue) for sending emails.
"""

from typing import List, Optional, Dict, Any
from models import Opportunity
from external.brevo.client import get_brevo_client
from external.email.templates import (
    get_new_opportunity_email_subject,
    get_updated_opportunity_email_subject,
    get_new_opportunity_email_html,
    get_updated_opportunity_email_html,
    get_new_opportunity_email_text,
    get_updated_opportunity_email_text,
    get_daily_summary_email_subject,
    get_daily_summary_email_html,
    get_daily_summary_email_text,
)
from core.config import settings
from core.exceptions import BrevoError
from core.logging import get_logger

logger = get_logger(__name__)


class EmailSender:
    """Email sender for opportunity notifications."""
    
    def __init__(self):
        self.brevo_client = get_brevo_client()
        self.base_url = settings.frontend_url
    
    def is_configured(self) -> bool:
        """Check if email sending is configured."""
        return self.brevo_client.is_configured() and bool(settings.brevo_sender_email)
    
    def send_new_opportunity_notification(
        self,
        opportunity: Opportunity,
        subscriber_emails: List[str]
    ) -> Dict[str, Any]:
        """
        Send new opportunity notification to subscribers.
        
        Args:
            opportunity: Opportunity object
            subscriber_emails: List of email addresses to notify
            
        Returns:
            Dictionary with send results
        """
        if not self.is_configured():
            logger.warning("Brevo not configured, skipping email notification")
            return {"sent": 0, "failed": len(subscriber_emails), "errors": ["Brevo not configured"]}
        
        if not subscriber_emails:
            logger.info("No subscribers to notify")
            return {"sent": 0, "failed": 0, "errors": []}
        
        subject = get_new_opportunity_email_subject(opportunity)
        html_content = get_new_opportunity_email_html(opportunity, self.base_url)
        text_content = get_new_opportunity_email_text(opportunity)
        
        results = {"sent": 0, "failed": 0, "errors": []}
        
        for email in subscriber_emails:
            try:
                self._send_email(
                    to_email=email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content
                )
                results["sent"] += 1
                logger.info(f"Sent new opportunity notification to {email}")
            except Exception as e:
                results["failed"] += 1
                error_msg = f"Failed to send to {email}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        return results
    
    def send_updated_opportunity_notification(
        self,
        opportunity: Opportunity,
        changed_fields: List[str],
        subscriber_emails: List[str]
    ) -> Dict[str, Any]:
        """
        Send updated opportunity notification to subscribers.
        
        Args:
            opportunity: Opportunity object
            changed_fields: List of field names that changed
            subscriber_emails: List of email addresses to notify
            
        Returns:
            Dictionary with send results
        """
        if not self.is_configured():
            logger.warning("Brevo not configured, skipping email notification")
            return {"sent": 0, "failed": len(subscriber_emails), "errors": ["Brevo not configured"]}
        
        if not subscriber_emails:
            logger.info("No subscribers to notify")
            return {"sent": 0, "failed": 0, "errors": []}
        
        subject = get_updated_opportunity_email_subject(opportunity, changed_fields)
        html_content = get_updated_opportunity_email_html(opportunity, changed_fields, self.base_url)
        text_content = get_updated_opportunity_email_text(opportunity, changed_fields)
        
        results = {"sent": 0, "failed": 0, "errors": []}
        
        for email in subscriber_emails:
            try:
                self._send_email(
                    to_email=email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content
                )
                results["sent"] += 1
                logger.info(f"Sent updated opportunity notification to {email}")
            except Exception as e:
                results["failed"] += 1
                error_msg = f"Failed to send to {email}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        return results
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> Optional[str]:
        """
        Send email via Brevo Transactional API.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content
            
        Returns:
            Brevo message ID if successful, None otherwise
            
        Raises:
            BrevoError: If sending fails
        """
        try:
            from sib_api_v3_sdk import TransactionalEmailsApi, SendSmtpEmail, SendSmtpEmailTo, SendSmtpEmailSender
            from sib_api_v3_sdk.rest import ApiException
            
            # Get sender email from settings
            sender_email = settings.brevo_sender_email
            sender_name = settings.brevo_sender_name
            
            if not sender_email:
                raise BrevoError("Brevo sender email not configured")
            
            # Create API instance
            api_key = settings.brevo_api_key
            if not api_key:
                raise BrevoError("Brevo API key not configured")
            
            from sib_api_v3_sdk import ApiClient, Configuration
            config = Configuration()
            config.api_key['api-key'] = api_key
            api_client = ApiClient(config)
            transactional_api = TransactionalEmailsApi(api_client)
            
            # Create email
            send_smtp_email = SendSmtpEmail(
                to=[SendSmtpEmailTo(email=to_email)],
                sender=SendSmtpEmailSender(email=sender_email, name=sender_name),
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            # Send email
            response = transactional_api.send_transac_email(send_smtp_email)
            message_id = response.message_id if hasattr(response, 'message_id') else None
            
            logger.info(f"Email sent successfully to {to_email}, message ID: {message_id}")
            return message_id
            
        except ApiException as e:
            logger.error(f"Brevo API error sending email to {to_email}: {e}")
            raise BrevoError(f"Brevo API error: {e}")
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            raise BrevoError(f"Failed to send email: {e}")
    
    def send_daily_summary_notification(
        self,
        new_opportunities: List[Opportunity],
        amended_opportunities: List[Opportunity],
        subscriber_emails: List[str]
    ) -> Dict[str, Any]:
        """
        Send daily summary email with all new and amended opportunities.
        
        Args:
            new_opportunities: List of newly created opportunities
            amended_opportunities: List of amended opportunities
            subscriber_emails: List of email addresses to notify
            
        Returns:
            Dictionary with send results
        """
        if not self.is_configured():
            logger.warning("Brevo not configured, skipping email notification")
            return {"sent": 0, "failed": len(subscriber_emails), "errors": ["Brevo not configured"]}
        
        if not subscriber_emails:
            logger.info("No subscribers to notify")
            return {"sent": 0, "failed": 0, "errors": []}
        
        # Only send if there are changes
        if not new_opportunities and not amended_opportunities:
            logger.info("No changes to report, skipping summary email")
            return {"sent": 0, "failed": 0, "errors": []}
        
        subject = get_daily_summary_email_subject(
            new_count=len(new_opportunities),
            amended_count=len(amended_opportunities)
        )
        html_content = get_daily_summary_email_html(
            new_opportunities=new_opportunities,
            amended_opportunities=amended_opportunities,
            base_url=self.base_url
        )
        text_content = get_daily_summary_email_text(
            new_opportunities=new_opportunities,
            amended_opportunities=amended_opportunities
        )
        
        results = {"sent": 0, "failed": 0, "errors": []}
        
        for email in subscriber_emails:
            try:
                self._send_email(
                    to_email=email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content
                )
                results["sent"] += 1
                logger.info(f"Sent daily summary notification to {email}")
            except Exception as e:
                results["failed"] += 1
                error_msg = f"Failed to send to {email}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        return results


def get_email_sender() -> EmailSender:
    """Get email sender instance."""
    return EmailSender()

