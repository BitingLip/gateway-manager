from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from enum import Enum

from common.models import TaskType, TaskStatus


class LLMPayload(BaseModel):
    """Payload for LLM inference"""
    text: str = Field(..., description="Input text for the model")
    max_tokens: int = Field(default=50, ge=1, le=2048, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    repetition_penalty: float = Field(default=1.1, ge=1.0, le=2.0, description="Repetition penalty")


class TTSPayload(BaseModel):
    """Payload for Text-to-Speech"""
    text: str = Field(..., description="Text to convert to speech")
    voice_id: Optional[str] = Field(default=None, description="Voice identifier")
    speed: float = Field(default=1.0, ge=0.1, le=3.0, description="Speech speed multiplier")
    pitch: float = Field(default=1.0, ge=0.1, le=3.0, description="Pitch multiplier")


class StableDiffusionPayload(BaseModel):
    """Payload for Stable Diffusion image generation"""
    prompt: str = Field(..., description="Text prompt for image generation")
    negative_prompt: Optional[str] = Field(default=None, description="Negative prompt")
    width: int = Field(default=512, ge=64, le=2048, description="Image width")
    height: int = Field(default=512, ge=64, le=2048, description="Image height")
    num_inference_steps: int = Field(default=20, ge=1, le=100, description="Number of denoising steps")
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0, description="Guidance scale")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


class ImageToTextPayload(BaseModel):
    """Payload for Image-to-Text (captioning)"""
    image_data: str = Field(..., description="Base64 encoded image data")
    max_tokens: int = Field(default=100, ge=1, le=500, description="Maximum tokens in caption")


class TaskRequest(BaseModel):
    """Main task request schema"""
    task_type: TaskType = Field(..., description="Type of task to execute")
    model_name: str = Field(..., description="Specific model to use")
    payload: Union[LLMPayload, TTSPayload, StableDiffusionPayload, ImageToTextPayload] = Field(
        ..., description="Task-specific payload"
    )
    priority: int = Field(default=5, ge=1, le=10, description="Task priority (1=highest, 10=lowest)")
    timeout: int = Field(default=300, ge=30, le=1800, description="Task timeout in seconds")


class TaskResponse(BaseModel):
    """Response for submitted task"""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    created_at: str = Field(..., description="Task creation timestamp")
    estimated_completion: Optional[str] = Field(default=None, description="Estimated completion time")


class TaskStatusResponse(BaseModel):
    """Response for task status query"""
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current status")
    progress: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Progress percentage")
    created_at: str = Field(..., description="Task creation timestamp")
    started_at: Optional[str] = Field(default=None, description="Task start timestamp")
    completed_at: Optional[str] = Field(default=None, description="Task completion timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    worker_id: Optional[str] = Field(default=None, description="ID of worker processing the task")


class TaskResult(BaseModel):
    """Task execution result"""
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Final status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Task output data")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")
    worker_id: Optional[str] = Field(default=None, description="Worker that processed the task")
    created_at: str = Field(..., description="Task creation timestamp")
    completed_at: Optional[str] = Field(default=None, description="Task completion timestamp")


class ClusterStatus(BaseModel):
    """Overall cluster status"""
    total_workers: int = Field(..., description="Total number of worker processes")
    active_workers: int = Field(..., description="Number of active workers")
    pending_tasks: int = Field(..., description="Number of pending tasks")
    running_tasks: int = Field(..., description="Number of currently running tasks")
    completed_tasks_today: int = Field(..., description="Tasks completed today")
    average_task_time: Optional[float] = Field(default=None, description="Average task execution time")
    gpu_utilization: List[Dict[str, Any]] = Field(default=[], description="Per-GPU utilization stats")


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: str = Field(..., description="Error timestamp")
