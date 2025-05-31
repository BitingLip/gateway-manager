"""
Cluster management routes
"""

from fastapi import APIRouter, HTTPException
import structlog

from app.core.auth import AUTH_DEPENDENCY
from common.models import ClusterStatus
from app.services.task_service import get_cluster_stats

router = APIRouter(tags=["cluster"], dependencies=[AUTH_DEPENDENCY])
logger = structlog.get_logger(__name__)


@router.get("/cluster/status", response_model=ClusterStatus)
async def get_cluster_stats_endpoint():
    """Get overall cluster status and statistics"""
    try:
        stats = get_cluster_stats()
        return ClusterStatus(**stats)
    except Exception as e:
        logger.error("Error getting cluster stats", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get cluster statistics")
