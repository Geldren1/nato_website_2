"""
API v1 routes.
"""

from fastapi import APIRouter
from . import opportunities
from . import subscribe
from . import feedback

router = APIRouter()

router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
router.include_router(subscribe.router, prefix="/subscribe", tags=["subscribe"])
router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])

