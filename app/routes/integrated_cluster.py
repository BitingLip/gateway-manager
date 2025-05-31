"""
Integrated Cluster Routes - Proxy to Cluster Manager Service

These routes provide a unified API for cluster management that forwards
requests to the cluster-manager service.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import structlog

from app.core.auth import AUTH_DEPENDENCY
from app.services.service_proxy import service_proxy

logger = structlog.get_logger(__name__)

# Create router with /api prefix to match CLI expectations
integrated_cluster_router = APIRouter(
    prefix="/api/workers",
    tags=["Cluster Management (Integrated)"],
    dependencies=[AUTH_DEPENDENCY]
)


@integrated_cluster_router.get("/")
async def list_workers(
    status: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0)
):
    """
    List workers from cluster-manager service
    
    - **status**: Filter by worker status (active, inactive, busy, etc.)
    - **limit**: Maximum number of workers to return
    - **offset**: Number of workers to skip
    """
    try:
        params = {}
        if status is not None:
            params["status"] = status
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
            
        result = await service_proxy.get_workers(**params)
        
        logger.info("Workers listed successfully", count=len(result.get("workers", [])))
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list workers", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve workers")


@integrated_cluster_router.get("/{worker_id}")
async def get_worker(worker_id: str):
    """
    Get detailed information about a specific worker
    
    - **worker_id**: Unique identifier of the worker
    """
    try:
        result = await service_proxy.get_worker(worker_id)
        
        logger.info("Worker info retrieved", worker_id=worker_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get worker info", worker_id=worker_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve worker information")


@integrated_cluster_router.get("/cluster/status")
async def get_cluster_status():
    """
    Get overall cluster status and statistics from cluster-manager
    """
    try:
        result = await service_proxy.get_cluster_status()
        
        logger.info("Cluster status retrieved")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get cluster status", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve cluster status")


# Health check endpoint for cluster manager
@integrated_cluster_router.get("/health/check")
async def check_cluster_service_health():
    """Check health of the cluster-manager service"""
    try:
        health_status = await service_proxy.check_service_health("cluster-manager")
        return health_status
        
    except Exception as e:
        logger.error("Cluster service health check failed", error=str(e), exc_info=True)
        return {
            "service": "cluster-manager",
            "status": "unhealthy",
            "error": str(e)
        }
