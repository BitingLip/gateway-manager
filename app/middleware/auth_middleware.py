"""
Authentication middleware for Gateway Manager
"""

from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.models import AuthenticationService

logger = structlog.get_logger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication"""
    
    def __init__(self, app, auth_service: AuthenticationService):
        super().__init__(app)
        self.auth_service = auth_service
        
        # Paths that don't require authentication
        self.public_paths = {
            "/health",
            "/metrics", 
            "/docs",
            "/openapi.json",
            "/redoc"
        }
        
        # Paths that require authentication
        self.protected_prefixes = [
            "/api/",
            "/admin/",
            "/manage/"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Check if path requires authentication
        if not self._requires_auth(request.url.path):
            return await call_next(request)
        
        # Extract API key from request
        api_key = self._extract_api_key(request)
        
        if not api_key:
            logger.warning("Missing API key",
                          path=request.url.path,
                          client_ip=self._get_client_ip(request))
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate API key
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        key_data = await self.auth_service.validate_api_key(
            api_key=api_key,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        if not key_data:
            logger.warning("Invalid API key",
                          path=request.url.path,
                          client_ip=client_ip,
                          api_key_prefix=api_key[:10] + "..." if len(api_key) > 10 else api_key)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Store auth info in request state
        request.state.auth_user = key_data['name']
        request.state.auth_method = "api_key"
        request.state.api_key_id = key_data['key_id']
        request.state.rate_limit = key_data.get('rate_limit')
        request.state.permissions = key_data.get('permissions', [])
        
        logger.info("Authentication successful",
                   key_name=key_data['name'],
                   key_id=key_data['key_id'],
                   path=request.url.path,
                   client_ip=client_ip)
        
        return await call_next(request)
    
    def _requires_auth(self, path: str) -> bool:
        """Check if path requires authentication"""
        # Public paths don't require auth
        if path in self.public_paths:
            return False
        
        # Check protected prefixes
        return any(path.startswith(prefix) for prefix in self.protected_prefixes)
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers"""
        # Check Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header:
            if auth_header.startswith("Bearer "):
                return auth_header[7:]  # Remove "Bearer " prefix
            elif auth_header.startswith("ApiKey "):
                return auth_header[7:]  # Remove "ApiKey " prefix
        
        # Check X-API-Key header
        api_key_header = request.headers.get("x-api-key")
        if api_key_header:
            return api_key_header
        
        # Check query parameter
        api_key_param = request.query_params.get("api_key")
        if api_key_param:
            return api_key_param
        
        return None
    
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
