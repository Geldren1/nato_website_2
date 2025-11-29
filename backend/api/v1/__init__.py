"""
API v1 routes.
"""

from fastapi import APIRouter
from . import opportunities

router = APIRouter()

router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])

