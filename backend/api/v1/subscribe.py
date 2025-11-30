"""
Email Subscription API endpoints.
Manages subscriptions solely through Brevo.
"""

from fastapi import APIRouter, HTTPException
from services.subscription_service import SubscriptionService
from schemas.subscribe import (
    SubscribeRequest,
    SubscribeResponse,
    UnsubscribeRequest,
    UnsubscribeResponse
)
from core.exceptions import ValidationError
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()
subscription_service = SubscriptionService()


@router.post("", response_model=SubscribeResponse)
async def subscribe(request: SubscribeRequest):
    """
    Subscribe an email address to receive opportunity alerts.
    
    The email will be added to Brevo email service list.
    
    Args:
        request: Subscription request with email and optional preferences
        
    Returns:
        Subscription response
    """
    try:
        result = subscription_service.subscribe(request.email, request.preferences)
        return SubscribeResponse(**result)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error subscribing", event_type="api_error", email=request.email, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error subscribing: {str(e)}")


@router.post("/unsubscribe", response_model=UnsubscribeResponse)
async def unsubscribe(request: UnsubscribeRequest):
    """
    Unsubscribe an email address from opportunity alerts.
    
    Args:
        request: Unsubscribe request with email
        
    Returns:
        Unsubscribe response
    """
    try:
        result = subscription_service.unsubscribe(request.email)
        return UnsubscribeResponse(
            success=result["success"],
            message=result["message"]
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error unsubscribing", event_type="api_error", email=request.email, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error unsubscribing: {str(e)}")

