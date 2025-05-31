"""
Health check routes
"""

from fastapi import APIRouter
import time

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}


@router.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect"""
    return {"message": "GPU Cluster API Gateway", "docs": "/docs"}
