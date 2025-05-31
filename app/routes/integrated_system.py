"""
Integrated System Routes - Overall system monitoring and health checks

These routes provide system-wide monitoring and health checks for all
BitingLip services.
"""

from fastapi import APIRouter, HTTPException
import structlog
from datetime import datetime

from app.core.auth import AUTH_DEPENDENCY
from app.services.service_proxy import service_proxy

logger = structlog.get_logger(__name__)

# Create router for system-wide operations
integrated_system_router = APIRouter(
    prefix="/api/system",
    tags=["System Management (Integrated)"]
)

# Additional router for API compatibility
api_health_router = APIRouter(
    prefix="/api",
    tags=["API Compatibility"]
)


@integrated_system_router.get("/health")
async def get_system_health():
    """
    Get comprehensive health status of all BitingLip services
    
    This endpoint checks the health of:
    - model-manager service
    - task-manager service  
    - cluster-manager service
    - gateway itself
    
    Returns overall system status and individual service statuses.
    """
    try:
        # Check all services
        health_status = await service_proxy.check_all_services()
        
        logger.info(
            "System health check completed",
            overall_status=health_status["overall_status"],
            healthy_services=health_status["healthy_services"],
            total_services=health_status["total_services"]
        )
        
        return health_status
        
    except Exception as e:
        logger.error("System health check failed", error=str(e), exc_info=True)
        return {
            "overall_status": "error",
            "healthy_services": 0,
            "total_services": 3,
            "error": str(e),
            "services": {
                "model-manager": {"status": "unknown", "error": "Health check failed"},
                "task-manager": {"status": "unknown", "error": "Health check failed"},
                "cluster-manager": {"status": "unknown", "error": "Health check failed"}
            }
        }


@integrated_system_router.get("/status")
async def get_system_status():
    """
    Get comprehensive system status including service versions and capabilities
    """
    try:
        # Get health for all services
        health_status = await service_proxy.check_all_services()
        
        # Add gateway information
        gateway_info = {
            "name": "BitingLip Gateway",
            "version": "1.0.0",
            "status": "healthy",
            "capabilities": [
                "API routing",
                "Authentication",
                "Service proxy",
                "Health monitoring"
            ]
        }
        
        return {
            "system": {
                "name": "BitingLip AI Platform",
                "version": "1.0.0",
                "overall_status": health_status["overall_status"],
                "timestamp": health_status["timestamp"]
            },
            "gateway": gateway_info,
            "services": health_status["services"],
            "summary": {
                "healthy_services": health_status["healthy_services"],
                "total_services": health_status["total_services"],
                "availability_percentage": (health_status["healthy_services"] / health_status["total_services"]) * 100
            }
        }
        
    except Exception as e:
        logger.error("System status check failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")


# Endpoint for CLI to check gateway connectivity  
@integrated_system_router.get("/ping")
async def ping():
    """
    Simple ping endpoint for CLI connectivity testing
    """
    return {
        "status": "ok",
        "message": "BitingLip Gateway is running",
        "service": "gateway"
    }


# API compatibility endpoint for CLI health checks
@api_health_router.get("/health")
async def api_health():
    """
    API health endpoint for CLI compatibility
    Routes to the full system health check
    """
    try:
        # Get health for all services
        health_status = await service_proxy.check_all_services()
        
        return {
            "status": health_status["overall_status"],
            "timestamp": health_status["timestamp"],
            "services": health_status["services"],
            "healthy_services": health_status["healthy_services"],
            "total_services": health_status["total_services"]
        }
        
    except Exception as e:
        logger.error("API health check failed", error=str(e), exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "healthy_services": 0,
            "total_services": 0
        }
