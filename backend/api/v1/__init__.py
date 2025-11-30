"""
API v1 routes.
"""

from fastapi import APIRouter
from . import opportunities
from . import subscribe

router = APIRouter()

router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
router.include_router(subscribe.router, prefix="/subscribe", tags=["subscribe"])

