"""
Brevo API client wrapper.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from core.config import settings
from core.exceptions import BrevoError
from core.logging import get_logger

logger = get_logger(__name__)


class BrevoClient:
    """Client for Brevo API operations."""
    
    def __init__(self):
        """Initialize Brevo client."""
        self.api_key = settings.brevo_api_key
        self.list_id = settings.brevo_list_id
        self._client = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure Brevo client is initialized."""
        if self._initialized:
            return
        
        if not self.api_key:
            logger.warning("Brevo API key not configured")
            return
        
        try:
            from sib_api_v3_sdk import ApiClient, Configuration, ContactsApi
            from sib_api_v3_sdk.rest import ApiException
            
            config = Configuration()
            config.api_key['api-key'] = self.api_key
            api_client = ApiClient(config)
            self._client = ContactsApi(api_client)
            self._initialized = True
            logger.info("Brevo client initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize Brevo client: {e}")
            raise BrevoError(f"Failed to initialize Brevo client: {e}")
    
    def is_configured(self) -> bool:
        """
        Check if Brevo is configured.
        
        Returns:
            True if configured, False otherwise
        """
        return bool(self.api_key and self.list_id)
    
    def add_contact(
        self,
        email: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add email to Brevo contact list.
        
        Args:
            email: Email address
            preferences: Subscription preferences
            
        Returns:
            Brevo contact ID if successful, None otherwise
            
        Raises:
            BrevoError: If operation fails
        """
        if not self.is_configured():
            logger.warning("Brevo not configured, skipping contact addition")
            return None
        
        self._ensure_initialized()
        
        if not self._client:
            return None
        
        try:
            from sib_api_v3_sdk import CreateContact
            
            # Create contact
            contact = CreateContact(
                email=email,
                list_ids=[self.list_id],
                attributes={
                    'SUBSCRIPTION_DATE': datetime.utcnow().isoformat(),
                }
            )
            
            # Add preferences as attributes if provided
            if preferences:
                if 'opportunity_types' in preferences:
                    contact.attributes['OPPORTUNITY_TYPES'] = ','.join(preferences['opportunity_types'])
                if 'nato_bodies' in preferences:
                    contact.attributes['NATO_BODIES'] = ','.join(preferences['nato_bodies'])
                if 'notify_on_updates' in preferences:
                    contact.attributes['NOTIFY_ON_UPDATES'] = str(preferences['notify_on_updates'])
            
            try:
                response = self._client.create_contact(contact)
                logger.info(f"Added {email} to Brevo list {self.list_id}")
                return str(response.id) if hasattr(response, 'id') else None
            except Exception as e:
                # Contact might already exist, try to update
                if hasattr(e, 'status') and e.status == 400:
                    logger.info(f"Contact {email} may already exist in Brevo, attempting update...")
                    return self._update_contact(email, contact.attributes)
                else:
                    logger.warning(f"Brevo API error: {e}")
                    raise BrevoError(f"Failed to add contact to Brevo: {e}")
                    
        except BrevoError:
            raise
        except Exception as e:
            logger.error(f"Error adding to Brevo: {e}")
            raise BrevoError(f"Failed to add contact to Brevo: {e}")
    
    def _update_contact(self, email: str, attributes: Dict[str, Any]) -> Optional[str]:
        """
        Update existing contact in Brevo.
        
        Args:
            email: Email address
            attributes: Contact attributes
            
        Returns:
            Contact ID or "existing" if successful
        """
        try:
            from sib_api_v3_sdk import UpdateContact
            
            update_contact = UpdateContact(
                list_ids=[self.list_id],
                attributes=attributes
            )
            self._client.update_contact(email, update_contact)
            logger.info(f"Updated {email} in Brevo")
            return "existing"
        except Exception as e:
            logger.warning(f"Could not update contact in Brevo: {e}")
            return None
    
    def remove_contact(self, email: str) -> bool:
        """
        Remove contact from Brevo list (unsubscribe).
        
        Args:
            email: Email address
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            logger.warning("Brevo not configured, skipping contact removal")
            return False
        
        self._ensure_initialized()
        
        if not self._client:
            return False
        
        try:
            # Remove from list
            self._client.remove_contact_from_list(self.list_id, email)
            logger.info(f"Removed {email} from Brevo list {self.list_id}")
            return True
        except Exception as e:
            if hasattr(e, 'status') and e.status == 404:
                logger.info(f"Contact {email} not found in Brevo list")
                return True  # Already removed
            logger.warning(f"Error removing contact from Brevo: {e}")
            return False
    
    def get_contacts_from_list(self, limit: int = 50, offset: int = 0) -> list:
        """
        Get contacts from the Brevo list.
        
        Args:
            limit: Maximum number of contacts to return
            offset: Offset for pagination
            
        Returns:
            List of email addresses
        """
        if not self.is_configured():
            logger.warning("Brevo not configured, cannot fetch contacts")
            return []
        
        self._ensure_initialized()
        
        if not self._client:
            return []
        
        try:
            contacts = self._client.get_contacts_from_list(
                list_id=self.list_id,
                limit=limit,
                offset=offset
            )
            
            emails = []
            if hasattr(contacts, 'contacts') and contacts.contacts:
                for contact in contacts.contacts:
                    if hasattr(contact, 'email') and contact.email:
                        emails.append(contact.email)
            
            logger.info(f"Fetched {len(emails)} contacts from Brevo list {self.list_id}")
            return emails
        except Exception as e:
            logger.warning(f"Error fetching contacts from Brevo: {e}")
            return []


def get_brevo_client() -> BrevoClient:
    """
    Get Brevo client instance.
    
    Returns:
        BrevoClient instance
    """
    return BrevoClient()

