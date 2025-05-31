"""
Service Proxy - Routes requests to appropriate BitingLip services

This module handles routing and proxying requests from the gateway
to the appropriate microservices (model-manager, task-manager, cluster-manager).
"""

import httpx
import structlog
from typing import Dict, Any, Optional
from fastapi import HTTPException
from datetime import datetime

from app.config import settings

logger = structlog.get_logger(__name__)


class ServiceProxy:
    """Proxy for routing requests to BitingLip services"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.services = {
            "model-manager": settings.model_manager_url,
            "task-manager": settings.task_manager_url,
            "cluster-manager": settings.cluster_manager_url
        }
        
    async def cleanup(self):
        """Cleanup HTTP client"""
        await self.client.aclose()
    
    async def _make_request(
        self, 
        service: str, 
        method: str, 
        path: str, 
        **kwargs
    ) -> Dict[Any, Any]:
        """Make a request to a service and handle errors"""
        if service not in self.services:
            raise HTTPException(
                status_code=500, 
                detail=f"Unknown service: {service}"
            )
            
        url = f"{self.services[service]}{path}"
        
        try:
            logger.info(
                "Proxying request",
                service=service,
                method=method,
                url=url,
                path=path
            )
            
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "Service request failed",
                service=service,
                url=url,
                status_code=e.response.status_code,
                error=str(e)
            )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Service {service} error: {e.response.text}"
            )
            
        except httpx.RequestError as e:
            logger.error(
                "Service connection failed",
                service=service,
                url=url,
                error=str(e)
            )
            raise HTTPException(
                status_code=503,
                detail=f"Service {service} unavailable: {str(e)}"
            )
    
    # Model Manager proxy methods
    async def get_models(self, **params) -> Dict[Any, Any]:
        """Get available models from model-manager"""
        return await self._make_request(
            "model-manager", "GET", "/models", params=params
        )
    
    async def download_model(self, model_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Download a model via model-manager"""
        return await self._make_request(
            "model-manager", "POST", "/models/download", json=model_data
        )
    
    async def get_model_info(self, model_id: str) -> Dict[Any, Any]:
        """Get model information from model-manager"""
        return await self._make_request(
            "model-manager", "GET", f"/models/{model_id}"
        )
    
    async def delete_model(self, model_id: str) -> Dict[Any, Any]:
        """Delete a model via model-manager"""
        return await self._make_request(
            "model-manager", "DELETE", f"/models/{model_id}"
        )
    
    # Task Manager proxy methods
    async def submit_task(self, task_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Submit a task via task-manager"""
        return await self._make_request(
            "task-manager", "POST", "/tasks", json=task_data
        )
    
    async def get_task(self, task_id: str) -> Dict[Any, Any]:
        """Get task status from task-manager"""
        return await self._make_request(
            "task-manager", "GET", f"/tasks/{task_id}"
        )
    
    async def cancel_task(self, task_id: str) -> Dict[Any, Any]:
        """Cancel a task via task-manager"""
        return await self._make_request(
            "task-manager", "DELETE", f"/tasks/{task_id}"
        )
    
    async def get_tasks(self, **params) -> Dict[Any, Any]:
        """Get tasks list from task-manager"""
        return await self._make_request(
            "task-manager", "GET", "/tasks", params=params
        )
    
    async def get_worker_stats(self) -> Dict[Any, Any]:
        """Get worker statistics from task-manager"""
        return await self._make_request(
            "task-manager", "GET", "/tasks/workers/stats"
        )
    
    async def get_worker_health(self) -> Dict[Any, Any]:
        """Get worker health from task-manager"""
        return await self._make_request(
            "task-manager", "GET", "/tasks/workers/health"
        )
    
    # Cluster Manager proxy methods
    async def get_workers(self, **params) -> Dict[Any, Any]:
        """Get workers from cluster-manager"""
        return await self._make_request(
            "cluster-manager", "GET", "/workers", params=params
        )
    
    async def get_worker(self, worker_id: str) -> Dict[Any, Any]:
        """Get specific worker from cluster-manager"""
        return await self._make_request(
            "cluster-manager", "GET", f"/workers/{worker_id}"
        )
    
    async def get_cluster_status(self) -> Dict[Any, Any]:
        """Get cluster status from cluster-manager"""
        return await self._make_request(
            "cluster-manager", "GET", "/cluster/status"
        )
    
    # Health check methods
    async def check_service_health(self, service: str) -> Dict[str, Any]:
        """Check if a service is healthy"""
        try:
            result = await self._make_request(service, "GET", "/health")
            return {
                "service": service,
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "details": result
            }
        except Exception as e:
            return {
                "service": service,
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services"""
        results = {}
        for service in self.services.keys():
            results[service] = await self.check_service_health(service)
        
        healthy_count = sum(1 for r in results.values() if r["status"] == "healthy")
        
        return {
            "overall_status": "healthy" if healthy_count == len(results) else "degraded",
            "healthy_services": healthy_count,
            "total_services": len(results),
            "services": results,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global service proxy instance
service_proxy = ServiceProxy()
