"""
Integrated Task Routes - Proxy to Task Manager Service

These routes provide a unified API for task management that forwards
requests to the restructured task-manager service.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import structlog

from app.core.auth import AUTH_DEPENDENCY
from app.services.service_proxy import service_proxy

logger = structlog.get_logger(__name__)

# Create router with /api prefix to match CLI expectations
integrated_task_router = APIRouter(
    prefix="/api/tasks",
    tags=["Task Management (Integrated)"],
    dependencies=[AUTH_DEPENDENCY]
)


@integrated_task_router.post("/")
async def submit_task(task_data: Dict[Any, Any]):
    """
    Submit a new task to the task-manager service
    
    Expected payload:
    - **task_type**: Type of task (llm, tts, stable_diffusion, etc.)
    - **model_name**: Model to use for inference
    - **payload**: Task-specific input parameters
    - **priority**: Task priority (optional, 1=highest, 10=lowest)
    - **timeout**: Maximum execution time in seconds (optional)
    """
    try:
        # Validate required fields
        required_fields = ["task_type", "model_name", "payload"]
        for field in required_fields:
            if field not in task_data:
                raise HTTPException(status_code=400, detail=f"{field} is required")
                
        result = await service_proxy.submit_task(task_data)
        
        logger.info(
            "Task submitted successfully", 
            task_id=result.get("task_id"),
            task_type=task_data.get("task_type"),
            model_name=task_data.get("model_name")
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to submit task", 
            task_data=task_data, 
            error=str(e), 
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to submit task")


@integrated_task_router.get("/")
async def list_tasks(
    status: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0)
):
    """
    List tasks from task-manager service
    
    - **status**: Filter by task status (pending, running, completed, failed)
    - **limit**: Maximum number of tasks to return
    - **offset**: Number of tasks to skip
    """
    try:
        params = {}
        if status is not None:
            params["status"] = status
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
            
        result = await service_proxy.get_tasks(**params)
        
        logger.info("Tasks listed successfully", count=len(result.get("tasks", [])))
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list tasks", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")


@integrated_task_router.get("/{task_id}")
async def get_task(task_id: str):
    """
    Get detailed information about a specific task
    
    - **task_id**: Unique identifier of the task
    """
    try:
        result = await service_proxy.get_task(task_id)
        
        logger.info("Task info retrieved", task_id=task_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task info", task_id=task_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve task information")


@integrated_task_router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a running or pending task
    
    - **task_id**: Unique identifier of the task to cancel
    """
    try:
        result = await service_proxy.cancel_task(task_id)
        
        logger.info("Task cancelled", task_id=task_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel task", task_id=task_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel task")


# Worker monitoring endpoints
@integrated_task_router.get("/workers/stats")
async def get_worker_stats():
    """Get worker statistics from task-manager"""
    try:
        result = await service_proxy.get_worker_stats()
        
        logger.info("Worker stats retrieved")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get worker stats", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve worker statistics")


@integrated_task_router.get("/workers/health")
async def get_worker_health():
    """Get worker health status from task-manager"""
    try:
        result = await service_proxy.get_worker_health()
        
        logger.info("Worker health retrieved")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get worker health", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve worker health")


# Health check endpoint for task manager
@integrated_task_router.get("/health/check")
async def check_task_service_health():
    """Check health of the task-manager service"""
    try:
        health_status = await service_proxy.check_service_health("task-manager")
        return health_status
        
    except Exception as e:
        logger.error("Task service health check failed", error=str(e), exc_info=True)
        return {
            "service": "task-manager",
            "status": "unhealthy",
            "error": str(e)
        }
