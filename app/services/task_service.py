from celery import Celery
from typing import Dict, Any, Optional, cast
import uuid
import redis
import json
from datetime import datetime, timezone
import structlog

from app.config import settings
from common.models import TaskRequest, TaskType, TaskStatus
from app.schemas import TaskResult  # Keep gateway-specific schemas

logger = structlog.get_logger(__name__)

# Initialize Celery app
celery_app = Celery(
    'gpu_cluster_api',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    # include=['worker.app.tasks'] # Commented out
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    task_soft_time_limit=settings.task_soft_time_limit,
    task_time_limit=settings.task_time_limit,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_track_started=True
)

# Redis client for additional task metadata  
redis_client: redis.Redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def generate_task_id() -> str:
    """Generate a unique task ID"""
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()


def submit_task(task_request: TaskRequest) -> str:
    """
    Submit a task to the appropriate worker queue
    
    Args:
        task_request: The task request containing type, model, and payload
        
    Returns:
        str: Unique task ID
    """
    task_id = generate_task_id()
    created_at = get_current_timestamp()
    
    try:
        # Route task to appropriate worker based on task type
        task_name = _get_task_name(task_request.task_type)
        
        # Prepare task data
        task_data = {
            "task_id": task_id,
            "task_type": task_request.task_type.value,
            "model_name": task_request.model_name,
            "payload": task_request.input_data,
            "priority": task_request.priority,
            "timeout": task_request.timeout,
            "created_at": created_at
        }
        
        # Store task metadata in Redis
        metadata_key = f"task_metadata:{task_id}"
        redis_client.hset(metadata_key, mapping={
            "status": TaskStatus.PENDING.value,
            "created_at": created_at,
            "task_type": task_request.task_type.value,
            "model_name": task_request.model_name,
            "priority": task_request.priority,
            "timeout": task_request.timeout
        })
        redis_client.expire(metadata_key, 86400)  # Expire after 24 hours
        
        # Submit to Celery
        celery_result = celery_app.send_task(
            task_name,
            args=[task_data],
            task_id=task_id,
            priority=10 - (task_request.priority or 5),  # Celery uses reverse priority
            soft_time_limit=(task_request.timeout or 300) - 30,
            time_limit=task_request.timeout
        )
        
        logger.info(
            "Task submitted successfully",
            task_id=task_id,
            task_type=task_request.task_type.value,
            model_name=task_request.model_name
        )
        
        return task_id
        
    except Exception as e:
        logger.error(
            "Failed to submit task",
            task_id=task_id,
            error=str(e),
            task_type=task_request.task_type.value if task_request else "unknown"
        )
        # Update status to failure
        _update_task_status(task_id, TaskStatus.FAILURE, error_message=str(e))
        raise


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the current status of a task
    
    Args:
        task_id: The task identifier
        
    Returns:
        Dict containing task status information
    """
    try:        # Get metadata from Redis  
        metadata_key = f"task_metadata:{task_id}"
        metadata = cast(dict, redis_client.hgetall(metadata_key))
        
        if not metadata:
            return {
                "task_id": task_id,
                "status": "not_found",
                "error": "Task not found"
            }
        
        # Get Celery task info
        celery_result = celery_app.AsyncResult(task_id)
        
        # Determine current status
        if celery_result.state == "PENDING":
            status = TaskStatus.PENDING
        elif celery_result.state == "STARTED":
            status = TaskStatus.STARTED
        elif celery_result.state == "SUCCESS":
            status = TaskStatus.SUCCESS
        elif celery_result.state == "FAILURE":
            status = TaskStatus.FAILURE
        elif celery_result.state == "RETRY":
            status = TaskStatus.RETRY
        elif celery_result.state == "REVOKED":
            status = TaskStatus.REVOKED
        else:
            status = TaskStatus.PENDING
        
        result = {
            "task_id": task_id,
            "status": status.value,
            "created_at": metadata.get("created_at"),
            "started_at": metadata.get("started_at"),
            "completed_at": metadata.get("completed_at"),
            "worker_id": metadata.get("worker_id"),
            "progress": metadata.get("progress")
        }
        
        # Add error information if failed
        if status == TaskStatus.FAILURE:
            result["error_message"] = str(celery_result.info) if celery_result.info else "Unknown error"
        
        return result
        
    except Exception as e:
        logger.error("Failed to get task status", task_id=task_id, error=str(e))
        return {
            "task_id": task_id,
            "status": "error",
            "error": f"Failed to retrieve status: {str(e)}"
        }


def get_task_result(task_id: str) -> Optional[TaskResult]:
    """    Get the result of a completed task
    
    Args:
        task_id: The task identifier
        
    Returns:
        TaskResult if available, None otherwise
    """
    try:        # Get metadata from Redis
        metadata_key = f"task_metadata:{task_id}"
        metadata = cast(dict, redis_client.hgetall(metadata_key))
        
        if not metadata:
            return None
        
        # Get Celery result
        celery_result = celery_app.AsyncResult(task_id)
        
        if celery_result.state != "SUCCESS":
            return None
        
        # Extract result data
        result_data = celery_result.result
        
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            result=result_data.get("result") if result_data else None,
            metadata=result_data.get("metadata") if result_data else None,
            execution_time=float(metadata.get("execution_time", "0")),
            worker_id=metadata.get("worker_id"),
            created_at=metadata.get("created_at", ""),
            completed_at=metadata.get("completed_at")
        )
        
    except Exception as e:
        logger.error("Failed to get task result", task_id=task_id, error=str(e))
        return None


def cancel_task(task_id: str) -> bool:
    """
    Cancel a pending or running task
    
    Args:
        task_id: The task identifier
        
    Returns:
        bool: True if cancellation was successful
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        _update_task_status(task_id, TaskStatus.REVOKED)
        
        logger.info("Task cancelled", task_id=task_id)
        return True
        
    except Exception as e:
        logger.error("Failed to cancel task", task_id=task_id, error=str(e))
        return False


def get_cluster_stats() -> Dict[str, Any]:
    """
    Get cluster-wide statistics
    
    Returns:
        Dict containing cluster statistics
    """
    try:
        # Get active workers
        active_workers = celery_app.control.inspect().active()
        total_workers = len(active_workers) if active_workers else 0
        
        # Get queue lengths
        queue_info = celery_app.control.inspect().active_queues()
        
        # Count pending tasks (simplified)
        pending_tasks = 0
        running_tasks = 0
        
        if active_workers:
            for worker_tasks in active_workers.values():
                running_tasks += len(worker_tasks)
        
        return {
            "total_workers": total_workers,
            "active_workers": total_workers,  # Simplified - all workers are considered active if responding
            "pending_tasks": pending_tasks,
            "running_tasks": running_tasks,
            "completed_tasks_today": 0,  # TODO: Implement daily counter
            "average_task_time": None,  # TODO: Calculate from historical data
            "gpu_utilization": []  # TODO: Implement GPU monitoring
        }
        
    except Exception as e:
        logger.error("Failed to get cluster stats", error=str(e))
        return {
            "total_workers": 0,
            "active_workers": 0,
            "pending_tasks": 0,
            "running_tasks": 0,
            "completed_tasks_today": 0,
            "average_task_time": None,
            "gpu_utilization": []
        }


def _get_task_name(task_type: TaskType) -> str:
    """Map task type to Celery task name"""
    task_mapping = {
        TaskType.LLM: "app.tasks.run_llm_inference",
        TaskType.TTS: "app.tasks.run_tts_inference", 
        TaskType.STABLE_DIFFUSION: "app.tasks.run_sd_inference",
        TaskType.IMAGE_TO_TEXT: "app.tasks.run_image_to_text_inference"
    }
    return task_mapping.get(task_type, "app.tasks.run_llm_inference")


def _update_task_status(task_id: str, status: TaskStatus, **kwargs):
    """Update task status in Redis metadata"""
    try:
        metadata_key = f"task_metadata:{task_id}"
        update_data = {"status": status.value}
        
        if status == TaskStatus.STARTED:
            update_data["started_at"] = get_current_timestamp()
        elif status in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]:
            update_data["completed_at"] = get_current_timestamp()
        
        # Add any additional fields
        update_data.update(kwargs)
        
        redis_client.hset(metadata_key, mapping=update_data)
        
    except Exception as e:
        logger.error("Failed to update task status", task_id=task_id, error=str(e))
