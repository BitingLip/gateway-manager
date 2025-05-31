"""
Common models and enums shared across the BitingLip Gateway

This module contains the common data models and enums used throughout
the gateway application.
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from datetime import datetime


class TaskType(str, Enum):
    """Supported task types"""
    LLM = "llm"
    TTS = "tts"
    STABLE_DIFFUSION = "stable_diffusion"
    IMAGE_TO_TEXT = "image_to_text"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskRequest(BaseModel):
    """Task request model"""
    task_type: TaskType = Field(..., description="Type of task to execute")
    model_name: str = Field(..., description="Specific model to use")
    payload: Dict[str, Any] = Field(..., description="Task-specific input parameters")
    priority: int = Field(default=5, ge=1, le=10, description="Task priority (1=highest, 10=lowest)")
    timeout: int = Field(default=300, ge=30, le=1800, description="Task timeout in seconds")


class TaskResponse(BaseModel):
    """Task response model"""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    task_type: TaskType = Field(..., description="Type of task")
    model_name: str = Field(..., description="Model used for the task")
    created_at: datetime = Field(..., description="Task creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result data")
    error: Optional[str] = Field(None, description="Error message if failed")


class ClusterStatus(BaseModel):
    """Cluster status information"""
    total_workers: int = Field(..., description="Total number of workers")
    active_workers: int = Field(..., description="Number of active workers")
    busy_workers: int = Field(..., description="Number of busy workers")
    pending_tasks: int = Field(..., description="Number of pending tasks")
    running_tasks: int = Field(..., description="Number of running tasks")
    total_tasks_processed: int = Field(..., description="Total tasks processed")
    average_task_time: float = Field(..., description="Average task execution time in seconds")
    uptime: float = Field(..., description="Cluster uptime in seconds")


class WorkerInfo(BaseModel):
    """Worker information"""
    worker_id: str = Field(..., description="Unique worker identifier")
    status: str = Field(..., description="Worker status")
    hostname: str = Field(..., description="Worker hostname")
    gpu_info: Optional[Dict[str, Any]] = Field(None, description="GPU information")
    current_load: float = Field(..., description="Current CPU/GPU load")
    memory_usage: Dict[str, Any] = Field(..., description="Memory usage statistics")
    tasks_completed: int = Field(..., description="Number of tasks completed")
    last_heartbeat: datetime = Field(..., description="Last heartbeat timestamp")
