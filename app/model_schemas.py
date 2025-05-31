"""
Model Management API Schemas

Pydantic schemas for the model management REST API endpoints.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ModelType(str, Enum):
    """Supported model types"""
    LLM = "llm"
    TTS = "tts" 
    STABLE_DIFFUSION = "stable_diffusion"
    IMAGE_TO_TEXT = "image_to_text"
    MULTIMODAL = "multimodal"
    EMBEDDINGS = "embeddings"
    CUSTOM = "custom"


class ModelStatus(str, Enum):
    """Model status"""
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    LOADING = "loading"
    ERROR = "error"
    DELETED = "deleted"


class WorkerStatus(str, Enum):
    """Worker status"""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"


# Model Management Request/Response Schemas

class ModelDownloadRequest(BaseModel):
    """Request to download a model from HuggingFace"""
    model_id: str = Field(..., description="HuggingFace model identifier")
    model_type: Optional[ModelType] = Field(default=None, description="Model type (auto-detected if not provided)")
    force_download: bool = Field(default=False, description="Force re-download if model exists")


class ModelUploadRequest(BaseModel):
    """Request to register a local model"""
    model_name: str = Field(..., description="Name for the model")
    model_type: ModelType = Field(..., description="Type of model")
    model_path: str = Field(..., description="Local path to model files")
    description: Optional[str] = Field(default=None, description="Model description")
    tags: List[str] = Field(default=[], description="Model tags")


class ModelAssignRequest(BaseModel):
    """Request to assign a model to a worker"""
    model_name: str = Field(..., description="Model to assign")
    worker_id: Optional[str] = Field(default=None, description="Specific worker ID (auto-assign if not provided)")
    force: bool = Field(default=False, description="Force assignment even if worker is at capacity")


class ModelUnloadRequest(BaseModel):
    """Request to unload a model from a worker"""
    model_name: str = Field(..., description="Model to unload")
    worker_id: Optional[str] = Field(default=None, description="Specific worker (unload from all if not provided)")


class ModelSearchRequest(BaseModel):
    """Request to search HuggingFace models"""
    query: str = Field(..., description="Search query")
    model_type: Optional[ModelType] = Field(default=None, description="Filter by model type")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")


class ModelListRequest(BaseModel):
    """Request to list local models"""
    model_type: Optional[ModelType] = Field(default=None, description="Filter by model type")
    status: Optional[ModelStatus] = Field(default=None, description="Filter by status")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


# Response Schemas

class ModelInfo(BaseModel):
    """Basic model information"""
    model_name: str = Field(..., description="Model name")
    model_type: ModelType = Field(..., description="Model type")
    status: ModelStatus = Field(..., description="Current status")
    size_gb: Optional[float] = Field(default=None, description="Model size in GB")
    description: Optional[str] = Field(default=None, description="Model description")
    tags: List[str] = Field(default=[], description="Model tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ModelDownloadResponse(BaseModel):
    """Response for model download request"""
    model_name: str = Field(..., description="Downloaded model name")
    status: str = Field(..., description="Download status")
    download_id: str = Field(..., description="Download task ID for progress tracking")
    message: str = Field(..., description="Status message")


class ModelAssignResponse(BaseModel):
    """Response for model assignment"""
    model_name: str = Field(..., description="Assigned model")
    worker_id: str = Field(..., description="Worker assigned to")
    status: str = Field(..., description="Assignment status")
    message: str = Field(..., description="Status message")


class ModelSearchResult(BaseModel):
    """HuggingFace model search result"""
    model_id: str = Field(..., description="HuggingFace model ID")
    model_name: str = Field(..., description="Model display name")
    description: Optional[str] = Field(default=None, description="Model description")
    model_type: Optional[ModelType] = Field(default=None, description="Detected model type")
    downloads: Optional[int] = Field(default=None, description="Download count")
    likes: Optional[int] = Field(default=None, description="Number of likes")
    tags: List[str] = Field(default=[], description="Model tags")


class ModelListResponse(BaseModel):
    """Response for model listing"""
    models: List[ModelInfo] = Field(..., description="List of models")
    total: int = Field(..., description="Total number of models")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total pages")


class WorkerInfo(BaseModel):
    """Worker information"""
    worker_id: str = Field(..., description="Worker identifier")
    status: WorkerStatus = Field(..., description="Worker status")
    gpu_memory_total: float = Field(..., description="Total GPU memory in GB")
    gpu_memory_used: float = Field(..., description="Used GPU memory in GB")
    gpu_memory_free: float = Field(..., description="Free GPU memory in GB")
    models_loaded: List[str] = Field(default=[], description="Currently loaded models")
    load_score: float = Field(..., description="Current load score")
    last_seen: datetime = Field(..., description="Last heartbeat timestamp")


class ClusterStatusResponse(BaseModel):
    """Complete cluster status"""
    workers: List[WorkerInfo] = Field(..., description="Worker information")
    total_models: int = Field(..., description="Total models in registry")
    loaded_models: int = Field(..., description="Models currently loaded")
    total_memory_gb: float = Field(..., description="Total cluster GPU memory")
    used_memory_gb: float = Field(..., description="Used cluster GPU memory")
    memory_utilization: float = Field(..., description="Memory utilization percentage")
    active_downloads: int = Field(..., description="Active download tasks")


class DownloadProgressResponse(BaseModel):
    """Download progress information"""
    download_id: str = Field(..., description="Download task ID")
    model_name: str = Field(..., description="Model being downloaded")
    status: str = Field(..., description="Download status")
    progress_percent: Optional[float] = Field(default=None, description="Progress percentage")
    downloaded_mb: Optional[float] = Field(default=None, description="Downloaded data in MB")
    total_mb: Optional[float] = Field(default=None, description="Total size in MB")
    speed_mbps: Optional[float] = Field(default=None, description="Download speed in MB/s")
    eta_seconds: Optional[int] = Field(default=None, description="Estimated time remaining")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class SystemStatsResponse(BaseModel):
    """System statistics"""
    registry_stats: Dict[str, Any] = Field(..., description="Registry statistics")
    worker_stats: Dict[str, Any] = Field(..., description="Worker statistics")
    memory_stats: Dict[str, Any] = Field(..., description="Memory usage statistics")
    model_stats: Dict[str, Any] = Field(..., description="Model statistics")
    performance_stats: Dict[str, Any] = Field(..., description="Performance metrics")


# Generic Response Schemas

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = Field(default=True, description="Operation success")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")


class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = Field(default=False, description="Operation success")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
