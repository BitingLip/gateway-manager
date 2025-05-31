"""
Integrated Model Routes - Proxy to Model Manager Service

These routes provide a unified API for model management that forwards
requests to the restructured model-manager service.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
import structlog

from app.core.auth import AUTH_DEPENDENCY
from app.services.service_proxy import service_proxy

logger = structlog.get_logger(__name__)

# Create router with /api prefix to match CLI expectations
integrated_model_router = APIRouter(
    prefix="/api/models",
    tags=["Model Management (Integrated)"],
    dependencies=[AUTH_DEPENDENCY]
)


@integrated_model_router.get("/")
async def list_models(
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
    search: Optional[str] = Query(None)
):
    """
    List available models via model-manager service
    
    - **limit**: Maximum number of models to return
    - **offset**: Number of models to skip
    - **search**: Search term to filter models
    """
    try:
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if search is not None:
            params["search"] = search
            
        result = await service_proxy.get_models(**params)
        
        logger.info("Models listed successfully", count=len(result.get("models", [])))
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list models", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve models")


@integrated_model_router.get("/{model_id}")
async def get_model(model_id: str):
    """
    Get detailed information about a specific model
    
    - **model_id**: Unique identifier of the model
    """
    try:
        result = await service_proxy.get_model_info(model_id)
        
        logger.info("Model info retrieved", model_id=model_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get model info", model_id=model_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve model information")


@integrated_model_router.post("/download")
async def download_model(model_data: Dict[Any, Any]):
    """
    Download a model from HuggingFace Hub via model-manager
    
    Expected payload:
    - **model_id**: HuggingFace model identifier
    - **model_type**: Type of model (llm, embedding, etc.)
    - **force_download**: Whether to re-download if exists
    """
    try:
        # Validate required fields
        if "model_id" not in model_data:
            raise HTTPException(status_code=400, detail="model_id is required")
            
        result = await service_proxy.download_model(model_data)
        
        logger.info("Model download initiated", model_id=model_data.get("model_id"))
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to initiate model download", 
            model_data=model_data, 
            error=str(e), 
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to initiate model download")


@integrated_model_router.delete("/{model_id}")
async def delete_model(model_id: str):
    """
    Delete a model via model-manager service
    
    - **model_id**: Unique identifier of the model to delete
    """
    try:
        result = await service_proxy.delete_model(model_id)
        
        logger.info("Model deleted", model_id=model_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete model", model_id=model_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete model")


# Health check endpoint for model manager
@integrated_model_router.get("/health/check")
async def check_model_service_health():
    """Check health of the model-manager service"""
    try:
        health_status = await service_proxy.check_service_health("model-manager")
        return health_status
        
    except Exception as e:
        logger.error("Model service health check failed", error=str(e), exc_info=True)
        return {
            "service": "model-manager",
            "status": "unhealthy",
            "error": str(e)
        }
