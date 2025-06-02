"""
Middleware Factory - Creates middleware instances with proper dependency injection
"""

from typing import Optional
from fastapi import FastAPI

from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.auth_middleware import AuthenticationMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security_middleware import SecurityMiddleware

from app.models.api_request import APIRequestModel
from app.models.auth import AuthModel
from app.models.rate_limit import RateLimitModel
from app.models.security import SecurityModel


class MiddlewareFactory:
    """Factory for creating middleware instances with proper dependency injection"""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    def get_logging_middleware(self) -> LoggingMiddleware:
        """Create logging middleware with API request service"""
        api_request_model = getattr(self.app.state, 'api_request_model', None)
        if not api_request_model:
            raise RuntimeError("API request model not initialized in app state")
        return LoggingMiddleware(api_request_model)
    
    def get_auth_middleware(self) -> AuthenticationMiddleware:
        """Create authentication middleware with auth service"""
        auth_model = getattr(self.app.state, 'auth_model', None)
        if not auth_model:
            raise RuntimeError("Auth model not initialized in app state")
        return AuthenticationMiddleware(auth_model)
    
    def get_rate_limit_middleware(self) -> RateLimitMiddleware:
        """Create rate limiting middleware with rate limit and security services"""
        rate_limit_model = getattr(self.app.state, 'rate_limit_model', None)
        security_model = getattr(self.app.state, 'security_model', None)
        
        if not rate_limit_model:
            raise RuntimeError("Rate limit model not initialized in app state")
        if not security_model:
            raise RuntimeError("Security model not initialized in app state")
            
        return RateLimitMiddleware(rate_limit_model, security_model)
    
    def get_security_middleware(self) -> SecurityMiddleware:
        """Create security middleware with security service"""
        security_model = getattr(self.app.state, 'security_model', None)
        if not security_model:
            raise RuntimeError("Security model not initialized in app state")
        return SecurityMiddleware(security_model)


def setup_middleware_stack(app: FastAPI) -> None:
    """
    Setup the complete middleware stack with proper dependency injection
    This should be called after database models are initialized in app.state
    """
    factory = MiddlewareFactory(app)
    
    # Add our enhanced middleware stack (order matters!)
    # 1. Security middleware (first line of defense)
    security_middleware = factory.get_security_middleware()
    app.add_middleware(type(security_middleware), security_service=security_middleware.security_service)
    
    # 2. Rate limiting middleware 
    rate_limit_middleware = factory.get_rate_limit_middleware()
    app.add_middleware(
        type(rate_limit_middleware), 
        rate_limit_service=rate_limit_middleware.rate_limit_service,
        security_service=rate_limit_middleware.security_service
    )
    
    # 3. Authentication middleware
    auth_middleware = factory.get_auth_middleware()
    app.add_middleware(type(auth_middleware), auth_service=auth_middleware.auth_service)
    
    # 4. Logging middleware (logs everything including auth results)
    logging_middleware = factory.get_logging_middleware()
    app.add_middleware(type(logging_middleware), db_service=logging_middleware.db_service)
