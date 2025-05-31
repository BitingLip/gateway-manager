"""
Model Management Service Layer - Minimal Working Version

Provides basic model management operations for the API.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import structlog

# Add the worker app to the path so we can import our model management components
sys.path.append(str(Path(__file__).parent.parent.parent / "worker"))

from app.model_schemas import (
    ModelDownloadResponse, ModelAssignResponse, ModelInfo, 
    ModelListResponse, ModelSearchResult, ClusterStatusResponse,
    DownloadProgressResponse, SystemStatsResponse, WorkerStatus,
    ModelType, ModelStatus, WorkerInfo
)

logger = structlog.get_logger(__name__)


class ModelManagementService:
    """
    Minimal model management service for Day 4 implementation.
    This provides a working API while we refine the integration.
    """
    
    def __init__(
        self, 
        registry_path: str = "models.db",
        models_dir: str = "./models"
    ):
        """Initialize the model management service."""
        self.registry_path = registry_path
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Active download tracking
        self._active_downloads: Dict[str, Dict[str, Any]] = {}
        
        # Initialize service state
        self._initialized = False
        
        # Mock data for testing
        self._mock_models = [
            {
                "model_name": "microsoft/DialoGPT-medium",
                "model_type": ModelType.LLM,
                "status": ModelStatus.AVAILABLE,
                "size_gb": 1.2,
                "description": "Conversational AI model",
                "tags": ["conversational", "gpt"],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            },
            {
                "model_name": "stabilityai/stable-diffusion-v1-4",
                "model_type": ModelType.STABLE_DIFFUSION,
                "status": ModelStatus.AVAILABLE,
                "size_gb": 4.5,
                "description": "Text-to-image generation model",
                "tags": ["diffusion", "image-generation"],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]
        
        # Mock workers
        self._mock_workers = [
            {
                "worker_id": "gpu-worker-1",
                "status": WorkerStatus.ONLINE,
                "gpu_memory_total": 24.0,
                "gpu_memory_used": 8.5,
                "gpu_memory_free": 15.5,
                "models_loaded": ["microsoft/DialoGPT-medium"],
                "load_score": 0.35,
                "last_seen": datetime.now()
            },
            {
                "worker_id": "gpu-worker-2", 
                "status": WorkerStatus.ONLINE,
                "gpu_memory_total": 16.0,
                "gpu_memory_used": 4.5,
                "gpu_memory_free": 11.5,
                "models_loaded": ["stabilityai/stable-diffusion-v1-4"],
                "load_score": 0.28,
                "last_seen": datetime.now()
            }
        ]
        
        logger.info(
            "Model management service initialized",
            registry_path=registry_path,
            models_dir=models_dir
        )
    
    async def download_model(
        self, 
        model_id: str, 
        model_type: Optional[ModelType] = None,
        force_download: bool = False
    ) -> ModelDownloadResponse:
        """
        Download a model from HuggingFace Hub.
        
        Args:
            model_id: HuggingFace model identifier
            model_type: Model type (auto-detected if None)
            force_download: Force re-download if model exists
            
        Returns:
            ModelDownloadResponse with download information
        """
        try:
            # Check if model already exists
            existing_model = next((m for m in self._mock_models if m["model_name"] == model_id), None)
            if existing_model and not force_download:
                return ModelDownloadResponse(
                    model_name=model_id,
                    status="exists",
                    download_id="",
                    message=f"Model {model_id} already exists in registry"
                )
            
            # Generate download ID
            download_id = f"dl_{int(datetime.now().timestamp())}_{model_id.replace('/', '_')}"
            
            # Start download in background
            asyncio.create_task(self._download_model_task(
                model_id, model_type, force_download, download_id
            ))
            
            return ModelDownloadResponse(
                model_name=model_id,
                status="started",
                download_id=download_id,
                message=f"Download started for {model_id}"
            )
            
        except Exception as e:
            logger.error("Failed to start model download", model_id=model_id, error=str(e))
            raise
    
    async def _download_model_task(
        self, 
        model_id: str, 
        model_type: Optional[ModelType],
        force_download: bool,
        download_id: str
    ):
        """Background task for model download."""
        try:
            # Track download progress
            self._active_downloads[download_id] = {
                "model_id": model_id,
                "status": "downloading",
                "progress_percent": 0,
                "started_at": datetime.now(),
                "error": None
            }
            
            # Simulate download progress
            for progress in [25, 50, 75, 100]:
                await asyncio.sleep(1)  # Simulate download time
                self._active_downloads[download_id]["progress_percent"] = progress
            
            # Add model to mock registry
            new_model = {
                "model_name": model_id,
                "model_type": model_type or ModelType.CUSTOM,
                "status": ModelStatus.AVAILABLE,
                "size_gb": 2.5,  # Mock size
                "description": f"Downloaded model: {model_id}",
                "tags": ["downloaded"],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            self._mock_models.append(new_model)
            
            # Update download status
            self._active_downloads[download_id].update({
                "status": "completed",
                "progress_percent": 100,
                "completed_at": datetime.now(),
                "model_path": str(self.models_dir / model_id)
            })
            
            logger.info("Model download completed", model_id=model_id, download_id=download_id)
            
        except Exception as e:
            # Update download status with error
            self._active_downloads[download_id].update({
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now()
            })
            logger.error("Model download failed", model_id=model_id, download_id=download_id, error=str(e))
    
    async def assign_model(
        self, 
        model_name: str, 
        worker_id: Optional[str] = None,
        force: bool = False
    ) -> ModelAssignResponse:
        """
        Assign a model to a worker.
        
        Args:
            model_name: Model to assign
            worker_id: Specific worker (auto-assign if None)
            force: Force assignment even if worker is at capacity
            
        Returns:
            ModelAssignResponse with assignment information
        """
        try:
            # Check if model exists
            model = next((m for m in self._mock_models if m["model_name"] == model_name), None)
            if not model:
                raise ValueError(f"Model {model_name} not found in registry")
            
            # Find available worker
            if worker_id:
                worker = next((w for w in self._mock_workers if w["worker_id"] == worker_id), None)
                if not worker:
                    raise ValueError(f"Worker {worker_id} not found")
            else:
                # Find worker with most free memory
                worker = max(self._mock_workers, key=lambda w: w["gpu_memory_free"])
            
            # Simulate assignment
            if model_name not in worker["models_loaded"]:
                worker["models_loaded"].append(model_name)
                worker["gpu_memory_used"] += model["size_gb"]
                worker["gpu_memory_free"] -= model["size_gb"]
            
            return ModelAssignResponse(
                model_name=model_name,
                worker_id=worker["worker_id"],
                status="assigned",
                message=f"Model {model_name} assigned to worker {worker['worker_id']}"
            )
                
        except Exception as e:
            logger.error("Failed to assign model", model_name=model_name, worker_id=worker_id, error=str(e))
            raise
    
    async def unload_model(
        self, 
        model_name: str, 
        worker_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unload a model from worker(s).
        
        Args:
            model_name: Model to unload
            worker_id: Specific worker (unload from all if None)
            
        Returns:
            Dictionary with unload results
        """
        try:
            unloaded_from = []
            
            for worker in self._mock_workers:
                if worker_id and worker["worker_id"] != worker_id:
                    continue
                    
                if model_name in worker["models_loaded"]:
                    worker["models_loaded"].remove(model_name)
                    
                    # Find model size to free memory
                    model = next((m for m in self._mock_models if m["model_name"] == model_name), None)
                    if model:
                        worker["gpu_memory_used"] -= model["size_gb"]
                        worker["gpu_memory_free"] += model["size_gb"]
                    
                    unloaded_from.append(worker["worker_id"])
            
            return {
                "success": True,
                "message": f"Model {model_name} unloaded from {len(unloaded_from)} workers",
                "workers": unloaded_from
            }
            
        except Exception as e:
            logger.error("Failed to unload model", model_name=model_name, worker_id=worker_id, error=str(e))
            raise
    
    async def list_models(
        self, 
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> ModelListResponse:
        """
        List models in the registry.
        
        Args:
            model_type: Filter by model type
            status: Filter by status
            page: Page number
            page_size: Items per page
            
        Returns:
            ModelListResponse with paginated model list
        """
        try:
            # Filter models
            filtered_models = self._mock_models.copy()
            
            if model_type:
                filtered_models = [m for m in filtered_models if m["model_type"] == model_type]
            
            if status:
                filtered_models = [m for m in filtered_models if m["status"] == status]
            
            # Apply pagination
            total = len(filtered_models)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_models = filtered_models[start_idx:end_idx]
            
            # Convert to response format
            model_infos = []
            for model in paginated_models:
                model_infos.append(ModelInfo(
                    model_name=model["model_name"],
                    model_type=model["model_type"],
                    status=model["status"],
                    size_gb=model["size_gb"],
                    description=model["description"],
                    tags=model["tags"],
                    created_at=model["created_at"],
                    updated_at=model["updated_at"]
                ))
            
            pages = (total + page_size - 1) // page_size
            
            return ModelListResponse(
                models=model_infos,
                total=total,
                page=page,
                page_size=page_size,
                pages=pages
            )
            
        except Exception as e:
            logger.error("Failed to list models", error=str(e))
            raise
    
    async def search_huggingface_models(
        self, 
        query: str, 
        model_type: Optional[ModelType] = None,
        limit: int = 20
    ) -> List[ModelSearchResult]:
        """
        Search HuggingFace Hub for models.
        
        Args:
            query: Search query
            model_type: Filter by model type
            limit: Maximum results
            
        Returns:
            List of ModelSearchResult
        """
        try:
            # Mock HuggingFace search results
            mock_results = [
                {
                    "model_id": f"huggingface/{query}-model-{i}",
                    "model_name": f"{query.title()} Model {i}",
                    "description": f"A {query} model for various tasks",
                    "model_type": model_type or ModelType.CUSTOM,
                    "downloads": 1000 + i * 100,
                    "likes": 50 + i * 10,
                    "tags": [query, "huggingface", "popular"]
                }
                for i in range(1, min(limit + 1, 6))
            ]
            
            # Convert to response format
            search_results = []
            for result in mock_results:
                search_results.append(ModelSearchResult(
                    model_id=result["model_id"],
                    model_name=result["model_name"],
                    description=result["description"],
                    model_type=result["model_type"],
                    downloads=result["downloads"],
                    likes=result["likes"],
                    tags=result["tags"]
                ))
            
            return search_results
            
        except Exception as e:
            logger.error("Failed to search HuggingFace models", query=query, error=str(e))
            raise
    
    async def get_cluster_status(self) -> ClusterStatusResponse:
        """
        Get comprehensive cluster status.
        
        Returns:
            ClusterStatusResponse with complete cluster information
        """
        try:
            # Convert workers to response format
            workers_info = []
            for worker_data in self._mock_workers:
                workers_info.append(WorkerInfo(
                    worker_id=worker_data["worker_id"],
                    status=worker_data["status"],
                    gpu_memory_total=worker_data["gpu_memory_total"],
                    gpu_memory_used=worker_data["gpu_memory_used"],
                    gpu_memory_free=worker_data["gpu_memory_free"],
                    models_loaded=worker_data["models_loaded"],
                    load_score=worker_data["load_score"],
                    last_seen=worker_data["last_seen"]
                ))
            
            total_memory = sum(w.gpu_memory_total for w in workers_info)
            used_memory = sum(w.gpu_memory_used for w in workers_info)
            
            return ClusterStatusResponse(
                workers=workers_info,
                total_models=len(self._mock_models),
                loaded_models=sum(len(w.models_loaded) for w in workers_info),
                total_memory_gb=total_memory,
                used_memory_gb=used_memory,
                memory_utilization=used_memory / total_memory * 100 if total_memory > 0 else 0,
                active_downloads=len([d for d in self._active_downloads.values() if d["status"] == "downloading"])
            )
            
        except Exception as e:
            logger.error("Failed to get cluster status", error=str(e))
            raise
    
    async def get_download_progress(self, download_id: str) -> DownloadProgressResponse:
        """
        Get download progress information.
        
        Args:
            download_id: Download task ID
            
        Returns:
            DownloadProgressResponse with progress information
        """
        if download_id not in self._active_downloads:
            raise ValueError(f"Download ID {download_id} not found")
        
        download_info = self._active_downloads[download_id]
        
        return DownloadProgressResponse(
            download_id=download_id,
            model_name=download_info["model_id"],
            status=download_info["status"],
            progress_percent=download_info.get("progress_percent"),
            downloaded_mb=download_info.get("downloaded_mb", 0),
            total_mb=download_info.get("total_mb", 100),
            speed_mbps=download_info.get("speed_mbps", 10.5),
            eta_seconds=download_info.get("eta_seconds", 30),
            error_message=download_info.get("error")
        )
    
    async def get_system_statistics(self) -> SystemStatsResponse:
        """
        Get comprehensive system statistics.
        
        Returns:
            SystemStatsResponse with detailed statistics
        """
        try:
            # Calculate statistics
            worker_stats = {
                "total_workers": len(self._mock_workers),
                "active_workers": len([w for w in self._mock_workers if w["status"] == WorkerStatus.ONLINE]),
                "average_load": sum(w["load_score"] for w in self._mock_workers) / len(self._mock_workers) if self._mock_workers else 0
            }
            
            total_memory = sum(w["gpu_memory_total"] for w in self._mock_workers)
            used_memory = sum(w["gpu_memory_used"] for w in self._mock_workers)
            
            memory_stats = {
                "total_memory_gb": total_memory,
                "used_memory_gb": used_memory,
                "free_memory_gb": total_memory - used_memory,
                "utilization_percent": used_memory / total_memory * 100 if total_memory > 0 else 0
            }
            
            model_stats = {
                "total_models": len(self._mock_models),
                "loaded_models": sum(len(w["models_loaded"]) for w in self._mock_workers),
                "available_models": len([m for m in self._mock_models if m["status"] == ModelStatus.AVAILABLE]),
                "downloading_models": len([d for d in self._active_downloads.values() if d["status"] == "downloading"])
            }
            
            performance_stats = {
                "active_downloads": len([d for d in self._active_downloads.values() if d["status"] == "downloading"]),
                "completed_downloads": len([d for d in self._active_downloads.values() if d["status"] == "completed"]),
                "failed_downloads": len([d for d in self._active_downloads.values() if d["status"] == "error"])
            }
            
            registry_stats = {
                "total_models": len(self._mock_models),
                "models_by_type": {},
                "models_by_status": {}
            }
            
            return SystemStatsResponse(
                registry_stats=registry_stats,
                worker_stats=worker_stats,
                memory_stats=memory_stats,
                model_stats=model_stats,
                performance_stats=performance_stats
            )
            
        except Exception as e:
            logger.error("Failed to get system statistics", error=str(e))
            raise
    
    async def cleanup_downloads(self, max_age_hours: int = 24):
        """Clean up old download tracking data."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for download_id, info in self._active_downloads.items():
            if info["started_at"].timestamp() < cutoff_time:
                to_remove.append(download_id)
        
        for download_id in to_remove:
            del self._active_downloads[download_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old download records")
    
    def register_worker_heartbeat(
        self,
        worker_id: str,
        gpu_memory_total: float,
        gpu_memory_used: float,
        models_loaded: List[str]
    ):
        """Register a worker heartbeat."""
        try:
            # Update existing worker or add new one
            worker = next((w for w in self._mock_workers if w["worker_id"] == worker_id), None)
            
            if worker:
                worker.update({
                    "gpu_memory_total": gpu_memory_total,
                    "gpu_memory_used": gpu_memory_used,
                    "gpu_memory_free": gpu_memory_total - gpu_memory_used,
                    "models_loaded": models_loaded,
                    "last_seen": datetime.now(),
                    "status": WorkerStatus.ONLINE
                })
            else:
                # Add new worker
                new_worker = {
                    "worker_id": worker_id,
                    "status": WorkerStatus.ONLINE,
                    "gpu_memory_total": gpu_memory_total,
                    "gpu_memory_used": gpu_memory_used,
                    "gpu_memory_free": gpu_memory_total - gpu_memory_used,
                    "models_loaded": models_loaded,
                    "load_score": gpu_memory_used / gpu_memory_total if gpu_memory_total > 0 else 0,
                    "last_seen": datetime.now()
                }
                self._mock_workers.append(new_worker)
            
            logger.info(
                "Worker heartbeat registered",
                worker_id=worker_id,
                memory_total=gpu_memory_total,
                memory_used=gpu_memory_used,
                models=models_loaded
            )
            
        except Exception as e:
            logger.error("Failed to register worker heartbeat", worker_id=worker_id, error=str(e))
            raise

    async def initialize(self) -> None:
        """Initialize the model management service."""
        if self._initialized:
            return
            
        try:
            # Create necessary directories
            self.models_dir.mkdir(exist_ok=True)
            
            # Initialize any connections or resources
            logger.info("Model management service initialization complete")
            self._initialized = True
            
        except Exception as e:
            logger.error("Failed to initialize model management service", error=str(e))
            raise

    async def cleanup(self) -> None:
        """Cleanup model management service resources."""
        try:
            # Cancel any active downloads
            for download_id in list(self._active_downloads.keys()):
                logger.info("Cancelling active download", download_id=download_id)
                # In a real implementation, we'd cancel the download task
                del self._active_downloads[download_id]
            
            # Cleanup any other resources
            logger.info("Model management service cleanup complete")
            self._initialized = False
            
        except Exception as e:
            logger.error("Error during model management service cleanup", error=str(e))
            raise

    async def get_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get a single model by name."""
        for model in self._mock_models:
            if model["model_name"] == model_name:
                return model
        return None

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from the registry."""
        for i, model in enumerate(self._mock_models):
            if model["model_name"] == model_name:
                del self._mock_models[i]
                logger.info("Model deleted", model_name=model_name)
                return True
        return False

    async def rebalance_cluster(self) -> None:
        """Trigger cluster rebalancing."""
        logger.info("Cluster rebalancing triggered")
        # In a real implementation, this would redistribute models across workers
        # For now, we just log the action

    async def list_workers(self) -> List[WorkerInfo]:
        """
        List all workers in the cluster.
        
        Returns:
            List of WorkerInfo objects with current status
        """
        try:
            workers = []
            for worker_data in self._mock_workers:
                worker_info = WorkerInfo(
                    worker_id=worker_data["worker_id"],
                    status=worker_data["status"],
                    gpu_memory_total=worker_data["gpu_memory_total"],
                    gpu_memory_used=worker_data["gpu_memory_used"],
                    gpu_memory_free=worker_data["gpu_memory_free"],
                    models_loaded=worker_data["models_loaded"],
                    load_score=worker_data["load_score"],
                    last_seen=worker_data["last_seen"]
                )
                workers.append(worker_info)
            
            logger.info("Listed workers", worker_count=len(workers))
            return workers
            
        except Exception as e:
            logger.error("Failed to list workers", error=str(e))
            raise
