"""
Pydantic schemas for Email Subscription API.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict


class SubscribeRequest(BaseModel):
    """Email subscription request schema."""
    email: EmailStr
    preferences: Optional[Dict] = Field(
        default=None,
        description="Subscription preferences (e.g., opportunity_types, nato_bodies, notify_on_updates)"
    )


class SubscribeResponse(BaseModel):
    """Email subscription response schema."""
    success: bool
    message: str
    email: str


class UnsubscribeRequest(BaseModel):
    """Unsubscribe request schema."""
    email: EmailStr


class UnsubscribeResponse(BaseModel):
    """Unsubscribe response schema."""
    success: bool
    message: str

