"""
FastAPI backend for NATO Opportunities Website.
Handles opportunities from ACT IFIB.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from core.config import settings
from core.logging import get_logger

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NATO Opportunities API",
    description="API for NATO opportunities website - ACT IFIB",
    version="2.0.0",
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "message": "NATO Opportunities API",
        "status": "healthy",
        "version": "2.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

# Import and include v1 API router
from api.v1 import router as v1_router

# Include v1 API router
app.include_router(v1_router, prefix="/api/v1", tags=["v1"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

