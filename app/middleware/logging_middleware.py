"""
Logging middleware for Gateway Manager
"""

import time
import uuid
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.models import APIRequestService, APIRequest, get_db

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all API requests to database"""
    
    def __init__(self, app, db_service: APIRequestService):
        super().__init__(app)
        self.db_service = db_service
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = f"req_{uuid.uuid4().hex[:16]}"
        request.state.request_id = request_id
        
        # Extract request data
        start_time = time.time()
        
        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        # Get auth info if available
        auth_user = getattr(request.state, 'auth_user', None)
        auth_method = getattr(request.state, 'auth_method', None)
        
        # Get body size if available
        body_size = None
        if hasattr(request, '_body'):
            body_size = len(request._body)
        
        # Create API request record
        api_request = APIRequest(
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            body_size=body_size,
            client_ip=client_ip,
            user_agent=user_agent,
            auth_user=auth_user,
            auth_method=auth_method,
            target_service=self._extract_target_service(request.url.path)
        )
        
        # Log request start
        try:
            await self.db_service.log_request_start(api_request)
            logger.info("Request started",
                       request_id=request_id,
                       method=request.method,
                       path=str(request.url.path),
                       client_ip=client_ip)
        except Exception as e:
            logger.error("Failed to log request start",
                        request_id=request_id,
                        error=str(e))
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Get response size
            response_size = None
            if hasattr(response, 'body'):
                response_size = len(response.body)
            
            # Log request completion
            try:
                await self.db_service.complete_request(
                    request_id=request_id,
                    status_code=response.status_code,
                    response_size=response_size,
                    processing_time=processing_time
                )
                
                logger.info("Request completed",
                           request_id=request_id,
                           status_code=response.status_code,
                           processing_time=f"{processing_time:.3f}s")
                           
            except Exception as e:
                logger.error("Failed to log request completion",
                            request_id=request_id,
                            error=str(e))
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log error
            processing_time = time.time() - start_time
            
            try:
                await self.db_service.complete_request(
                    request_id=request_id,
                    status_code=500,
                    processing_time=processing_time,
                    error_message=str(e)
                )
            except Exception as log_error:
                logger.error("Failed to log request error",
                            request_id=request_id,
                            error=str(log_error))
            
            logger.error("Request failed",
                        request_id=request_id,
                        error=str(e),
                        processing_time=f"{processing_time:.3f}s")
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return "unknown"
    
    def _extract_target_service(self, path: str) -> str:
        """Extract target service from request path"""
        if path.startswith('/api/v1/'):
            parts = path.split('/')
            if len(parts) >= 4:
                return parts[3]  # /api/v1/{service}/...
        
        # Default mappings
        if path.startswith('/task'):
            return 'task-manager'
        elif path.startswith('/cluster'):
            return 'cluster-manager'
        elif path.startswith('/model'):
            return 'model-manager'
        elif path.startswith('/worker'):
            return 'worker'
        
        return 'gateway'
