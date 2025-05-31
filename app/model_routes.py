"""
Model Management API Routes

FastAPI routes for model management operations including:
- Model downloads from HuggingFace
- Model assignments to workers  
- Cluster status monitoring
- Model search and listing
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Request
from typing import Optional, List, Dict, Any
import structlog
import asyncio
from datetime import datetime

from app.services.model_service import ModelManagementService
from app.model_schemas import (
    # Request schemas
    ModelDownloadRequest, ModelUploadRequest, ModelAssignRequest,
    ModelUnloadRequest, ModelSearchRequest, ModelListRequest,
      # Response schemas
    ModelDownloadResponse, ModelAssignResponse, ModelInfo,
    ModelListResponse, ModelSearchResult, ClusterStatusResponse,
    DownloadProgressResponse, SystemStatsResponse, SuccessResponse,
    ErrorResponse, WorkerInfo,
    
    # Enums
    ModelType, ModelStatus
)

logger = structlog.get_logger(__name__)

# Create router
model_router = APIRouter(prefix="/models", tags=["Model Management"])


def get_model_service(request: Request) -> ModelManagementService:
    """Dependency to get the model service instance from app state."""
    if not hasattr(request.app.state, 'model_service'):
        raise HTTPException(
            status_code=500, 
            detail="Model management service not initialized"
        )
    return request.app.state.model_service


# Model Download and Management Endpoints

@model_router.post("/download", response_model=ModelDownloadResponse)
async def download_model(
    request: ModelDownloadRequest,
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Download a model from HuggingFace Hub.
    
    This endpoint starts a background download task and returns immediately
    with a download ID that can be used to track progress.
    """
    try:
        result = await service.download_model(
            model_id=request.model_id,
            model_type=request.model_type,
            force_download=request.force_download
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Download request failed", model_id=request.model_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@model_router.get("/download/{download_id}/progress", response_model=DownloadProgressResponse)
async def get_download_progress(
    download_id: str,
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Get progress information for a model download.
    
    Returns detailed progress including percentage, speed, and ETA.
    """
    try:
        result = await service.get_download_progress(download_id)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to get download progress", download_id=download_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@model_router.post("/assign", response_model=ModelAssignResponse)
async def assign_model(
    request: ModelAssignRequest,
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Assign a model to a worker.
    
    If no worker_id is specified, the system will automatically
    select the best available worker based on memory and load.
    """
    try:
        result = await service.assign_model(
            model_name=request.model_name,
            worker_id=request.worker_id,
            force=request.force
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Model assignment failed", model_name=request.model_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Assignment failed: {str(e)}")


@model_router.post("/unload", response_model=SuccessResponse)
async def unload_model(
    request: ModelUnloadRequest,
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Unload a model from worker(s).
    
    If no worker_id is specified, the model will be unloaded from all workers.
    """
    try:
        result = await service.unload_model(
            model_name=request.model_name,
            worker_id=request.worker_id
        )
        
        return SuccessResponse(
            message=result.get("message", "Model unloaded successfully"),
            data=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Model unload failed", model_name=request.model_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Unload failed: {str(e)}")


# Model Listing and Search Endpoints

@model_router.get("/", response_model=ModelListResponse)
async def list_models(
    model_type: Optional[ModelType] = Query(None, description="Filter by model type"),
    status: Optional[ModelStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ModelManagementService = Depends(get_model_service)
):
    """
    List models in the registry with optional filtering and pagination.
    """
    try:
        result = await service.list_models(
            model_type=model_type,
            status=status,
            page=page,            page_size=page_size
        )
        return result
        
    except Exception as e:
        logger.error("Failed to list models", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


# Health Check Endpoint - MUST be before /{model_name} route
@model_router.get("/health", response_model=Dict[str, Any])
async def health_check(
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Health check endpoint for the model management system.
    """
    try:
        # Basic connectivity checks
        registry_health = True
        try:
            await service.get_system_statistics()
        except Exception:
            registry_health = False
        
        cluster_health = True
        try:
            await service.get_cluster_status()
        except Exception:
            cluster_health = False
        
        overall_health = registry_health and cluster_health
        
        return {
            "status": "healthy" if overall_health else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "registry": "healthy" if registry_health else "unhealthy",
                "cluster": "healthy" if cluster_health else "unhealthy",
                "model_service": "healthy"
            }
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)        }


# Worker Management Endpoints - Must be before /{model_name} route

@model_router.get("/workers", response_model=List[WorkerInfo])
async def list_workers(
    service: ModelManagementService = Depends(get_model_service)
):
    """
    List all workers in the cluster with their current status and loaded models.
    """
    try:
        workers = await service.list_workers()
        return workers
        
    except Exception as e:
        logger.error("Failed to list workers", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list workers: {str(e)}")


@model_router.get("/{model_name}", response_model=ModelInfo)
async def get_model(
    model_name: str,
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Get detailed information about a specific model.
    """
    try:
        # Get model from registry
        model = await service.get_model(model_name)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        return ModelInfo(
            model_name=model["model_name"],
            model_type=model["model_type"],
            status=model["status"],
            size_gb=model["size_gb"],
            description=model["description"],
            tags=model["tags"],
            created_at=model["created_at"],
            updated_at=model["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get model", model_name=model_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get model: {str(e)}")


@model_router.delete("/{model_name}", response_model=SuccessResponse)
async def delete_model(
    model_name: str,
    force: bool = Query(False, description="Force delete even if model is loaded"),
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Delete a model from the registry and filesystem.
      Will fail if the model is currently loaded unless force=True.
    """
    try:
        # Check if model exists
        model = await service.get_model(model_name)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        # Check if model is loaded (if not forcing)
        if not force:
            cluster_status = await service.get_cluster_status()
            loaded_models = set()
            for worker in cluster_status.workers:
                loaded_models.update(worker.models_loaded)
            
            if model_name in loaded_models:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Model {model_name} is currently loaded. Use force=true to delete anyway."
                )
        
        # Unload from all workers first
        await service.unload_model(model_name)
        
        # Delete from registry
        await service.delete_model(model_name)
        
        return SuccessResponse(message=f"Model {model_name} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete model", model_name=model_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")


@model_router.get("/search/huggingface", response_model=List[ModelSearchResult])
async def search_huggingface_models(
    query: str = Query(..., description="Search query"),
    model_type: Optional[ModelType] = Query(None, description="Filter by model type"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Search HuggingFace Hub for models.
    
    Returns a list of models matching the search criteria.
    """
    try:
        results = await service.search_huggingface_models(
            query=query,
            model_type=model_type,
            limit=limit
        )
        return results
        
    except Exception as e:
        logger.error("HuggingFace search failed", query=query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Cluster Status and Monitoring Endpoints

@model_router.get("/cluster/status", response_model=ClusterStatusResponse)
async def get_cluster_status(
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Get comprehensive cluster status including workers, memory usage, and loaded models.
    """
    try:
        result = await service.get_cluster_status()
        return result
        
    except Exception as e:
        logger.error("Failed to get cluster status", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get cluster status: {str(e)}")


@model_router.get("/cluster/statistics", response_model=SystemStatsResponse)
async def get_system_statistics(
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Get detailed system statistics including registry, worker, and performance metrics.
    """
    try:
        result = await service.get_system_statistics()
        return result
        
    except Exception as e:
        logger.error("Failed to get system statistics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# Worker Management Endpoints

@model_router.post("/workers/{worker_id}/heartbeat", response_model=SuccessResponse)
async def worker_heartbeat(
    worker_id: str,
    gpu_memory_total: float = Query(..., description="Total GPU memory in GB"),
    gpu_memory_used: float = Query(..., description="Used GPU memory in GB"),
    models_loaded: str = Query("", description="Comma-separated list of loaded models"),
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Register a worker heartbeat with current status.
    
    Workers should call this endpoint regularly to maintain their active status.
    """
    try:        # Parse models list
        models = [m.strip() for m in models_loaded.split(",") if m.strip()]
        
        # Register heartbeat
        service.register_worker_heartbeat(
            worker_id=worker_id,
            gpu_memory_total=gpu_memory_total,
            gpu_memory_used=gpu_memory_used,
            models_loaded=models
        )
        
        return SuccessResponse(message=f"Heartbeat registered for worker {worker_id}")
        
    except Exception as e:
        logger.error("Failed to register worker heartbeat", worker_id=worker_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Heartbeat failed: {str(e)}")


@model_router.post("/cluster/rebalance", response_model=SuccessResponse)
async def rebalance_cluster(
    service: ModelManagementService = Depends(get_model_service)
):
    """
    Trigger cluster rebalancing to optimize model distribution across workers.
    """
    try:
        await service.rebalance_cluster()
        
        return SuccessResponse(            message="Cluster rebalancing completed"
        )
        
    except Exception as e:
        logger.error("Cluster rebalancing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Rebalancing failed: {str(e)}")
