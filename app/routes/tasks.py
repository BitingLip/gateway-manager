"""
Task management routes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from fastapi.responses import Response
from datetime import datetime, timezone
import structlog

from app.core.auth import AUTH_DEPENDENCY
from app.core.metrics import PENDING_TASKS
from common.models import TaskRequest, TaskResponse, TaskStatus
from app.schemas import TaskStatusResponse, TaskResult  # Keep gateway-specific schemas
from app.services.task_service import submit_task, get_task_status, get_task_result, cancel_task

router = APIRouter(tags=["tasks"], dependencies=[AUTH_DEPENDENCY])
logger = structlog.get_logger(__name__)


@router.post("/submit", response_model=TaskResponse)
async def submit_task_endpoint(
    task_request: TaskRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit a new task to the GPU cluster
    
    - **task_type**: Type of task (llm, tts, stable_diffusion, image_to_text)
    - **model_name**: Specific model to use for inference
    - **payload**: Task-specific input parameters
    - **priority**: Task priority (1=highest, 10=lowest)
    - **timeout**: Maximum execution time in seconds    """
    try:
        task_id = submit_task(task_request)
        PENDING_TASKS.inc()
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            task_type=task_request.task_type,
            model_name=task_request.model_name,
            created_at=datetime.now(timezone.utc)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error submitting task", error=str(e), task_request=task_request.dict(), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit task due to internal error")


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status_endpoint(task_id: str):
    """
    Get the current status of a task
    
    - **task_id**: Unique task identifier returned from submit endpoint
    """
    try:
        status_info = get_task_status(task_id)
        if status_info is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return status_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting task status", error=str(e), task_id=task_id, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.get("/tasks/{task_id}/result", response_model=TaskResult)
async def get_task_result_endpoint(task_id: str):
    """
    Get the result of a completed task
    
    - **task_id**: Unique task identifier
    """
    try:
        result_info = get_task_result(task_id)
        if result_info is None:
            raise HTTPException(status_code=404, detail="Task result not found or task not completed")
        return result_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting task result", error=str(e), task_id=task_id, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get task result")


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_task_endpoint(task_id: str, background_tasks: BackgroundTasks):
    """
    Cancel a pending or running task
    
    - **task_id**: Unique task identifier
    """
    try:
        success = cancel_task(task_id) 
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or could not be cancelled")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error cancelling task", error=str(e), task_id=task_id, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel task")
