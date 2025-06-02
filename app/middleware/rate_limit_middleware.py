"""
Rate limiting middleware for Gateway Manager
"""

from typing import Dict, Any
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.models import RateLimitService, SecurityService

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests"""
    
    def __init__(self, app, rate_limit_service: RateLimitService, 
                 security_service: SecurityService):
        super().__init__(app)
        self.rate_limit_service = rate_limit_service
        self.security_service = security_service
        
        # Paths exempt from rate limiting
        self.exempt_paths = {
            "/health",
            "/metrics"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Get rate limit parameters
        client_ip = self._get_client_ip(request)
        api_key_id = getattr(request.state, 'api_key_id', None)
        custom_limit = getattr(request.state, 'rate_limit', None)
        
        # Check rate limits
        rate_limit_results = []
        
        # 1. Check IP-based rate limit
        ip_result = await self.rate_limit_service.check_rate_limit(
            bucket_type="ip",
            identifier=client_ip,
            custom_limit={'requests': custom_limit, 'window': 3600} if custom_limit else None
        )
        rate_limit_results.append(('ip', ip_result))
        
        # 2. Check API key-based rate limit if authenticated
        if api_key_id:
            key_result = await self.rate_limit_service.check_rate_limit(
                bucket_type="api_key",
                identifier=api_key_id,
                custom_limit={'requests': custom_limit, 'window': 3600} if custom_limit else None
            )
            rate_limit_results.append(('api_key', key_result))
        
        # Check if any rate limit is exceeded
        blocked_results = [result for bucket_type, result in rate_limit_results if not result['allowed']]
        
        if blocked_results:
            # Use the most restrictive limit
            blocked_result = blocked_results[0]
            
            # Log rate limit violation
            logger.warning("Rate limit exceeded",
                          client_ip=client_ip,
                          api_key_id=api_key_id,
                          path=request.url.path,
                          reason=blocked_result['reason'])
            
            # Create security incident for rate limit violation
            try:
                await self.security_service.create_incident(
                    incident_type="rate_limit_exceeded",
                    severity="medium",
                    source_ip=client_ip,
                    description=f"Rate limit exceeded: {blocked_result['reason']}",
                    details={
                        "path": request.url.path,
                        "method": request.method,
                        "api_key_id": api_key_id,
                        "rate_limit_info": blocked_result
                    },
                    request_path=request.url.path,
                    request_method=request.method,
                    api_key_id=api_key_id
                )
            except Exception as e:
                logger.error("Failed to create rate limit incident", error=str(e))
            
            # Return rate limit error
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": blocked_result['reason'],
                    "retry_after": int(blocked_result['reset_time'].timestamp()) if blocked_result.get('reset_time') else None
                },
                headers={
                    "X-RateLimit-Limit": str(blocked_result.get('request_count', 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(blocked_result['reset_time'].timestamp())) if blocked_result.get('reset_time') else "",
                    "Retry-After": str(int((blocked_result['reset_time'] - request.state.start_time).total_seconds())) if blocked_result.get('reset_time') else "3600"
                }
            )
        
        # Store rate limit info for response headers
        allowed_result = rate_limit_results[0][1]  # Use first (IP) result for headers
        request.state.rate_limit_remaining = allowed_result.get('remaining', 0)
        request.state.rate_limit_reset = allowed_result.get('reset_time')
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        if hasattr(request.state, 'rate_limit_remaining'):
            response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
        
        if hasattr(request.state, 'rate_limit_reset'):
            reset_time = request.state.rate_limit_reset
            if reset_time:
                response.headers["X-RateLimit-Reset"] = str(int(reset_time.timestamp()))
        
        return response
    
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
