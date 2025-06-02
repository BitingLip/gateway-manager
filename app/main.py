"""
Gateway Manager - FastAPI Application Entry Point

This file is focused only on:
- Application setup and configuration
- Dependency injection setup
- Router registration  
- Middleware configuration

All business logic is in services/ and routes/
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from prometheus_client import start_http_server
import logging
import time

from app.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.core.auth import AUTH_DEPENDENCY
from app.routes import tasks, cluster, health
from app.model_routes import model_router
from app.services.model_service import ModelManagementService
from app.services.service_proxy import service_proxy

# Database models and services
from app.models.database import DatabaseManager
from app.models.api_request import APIRequestService
from app.models.auth import AuthenticationService
from app.models.rate_limit import RateLimitService
from app.models.security import SecurityService

# New integrated routes
from app.routes.integrated_models import integrated_model_router
from app.routes.integrated_tasks import integrated_task_router
from app.routes.integrated_cluster import integrated_cluster_router
from app.routes.integrated_system import integrated_system_router, api_health_router

# Admin management routes  
from app.routes.admin import router as admin_router

# Startup logging for API key configuration
logging.basicConfig(level=logging.INFO) 
startup_logger = logging.getLogger(f"{__name__}.startup_auth_check")
startup_logger.info(f"Auth Check at Startup: settings.api_key = '{settings.api_key}' (type: {type(settings.api_key)})")
if settings.api_key == "":
    startup_logger.warning("Auth Check at Startup: settings.api_key is an empty string. Treating as NO API key.")

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting GPU Cluster API Gateway", version="1.0.0", api_key_configured=bool(settings.api_key))
    
    # Initialize database manager
    db_manager = DatabaseManager()
    await db_manager.initialize()
    app.state.db_manager = db_manager
    logger.info("Database manager initialized")
      # Initialize database models
    app.state.api_request_service = APIRequestService(db_manager)
    app.state.auth_service = AuthenticationService(db_manager)
    app.state.rate_limit_service = RateLimitService(db_manager)
    app.state.security_service = SecurityService(db_manager)
    logger.info("Database models initialized")
    
    # Initialize model management service (legacy)
    model_service = ModelManagementService()
    await model_service.initialize()
    app.state.model_service = model_service
    logger.info("Model management service initialized")
    
    # Initialize service proxy for integrated routes
    app.state.service_proxy = service_proxy
    logger.info("Service proxy initialized for integrated routing")
    
    if settings.enable_prometheus:
        start_http_server(settings.prometheus_port)
        logger.info(f"Prometheus metrics server started on port {settings.prometheus_port}")
    
    yield
    
    # Cleanup database models
    if hasattr(app.state, 'db_manager'):
        await app.state.db_manager.close()
        logger.info("Database manager cleaned up")
    
    # Cleanup model service
    if hasattr(app.state, 'model_service'):
        await app.state.model_service.cleanup()
        logger.info("Model management service cleaned up")
    
    # Cleanup service proxy
    if hasattr(app.state, 'service_proxy'):
        await app.state.service_proxy.cleanup()
        logger.info("Service proxy cleaned up")
    
    logger.info("Shutting down GPU Cluster API Gateway")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    # Setup logging
    setup_logging()
    
    # Log authentication status
    if settings.api_key:
        logger.info("API Authentication: ENABLED. Routes will be protected by 'verify_api_key_if_configured'.", api_key_configured=True)
    else:
        logger.info("API Authentication: DISABLED. 'verify_api_key_if_configured' will allow all requests.", api_key_configured=False)

    app_description = (
        "REST API for AMD GPU cluster task submission and management. "
        + ("API key authentication is ENABLED and REQUIRED if an API_KEY is set in the environment." if settings.api_key else "API key authentication is DISABLED (open access).")
    )

    app = FastAPI(
        title="BitingLip GPU Cluster API Gateway",
        description=app_description,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware will be added after database initialization via startup event    @app.on_event("startup")
    async def setup_middleware():
        """Setup middleware after database models are initialized"""
        try:
            # Get service instances from app state
            api_request_service = app.state.api_request_service
            auth_service = app.state.auth_service
            rate_limit_service = app.state.rate_limit_service
            security_service = app.state.security_service
            
            # Add our enhanced middleware stack (order matters!)
            # Note: Using a simple request logging for now until middleware integration is fixed
            app.middleware("http")(create_enhanced_logging_middleware(api_request_service))
            
            logger.info("Enhanced middleware stack initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize middleware: {e}")
            # Fall back to basic logging
            app.middleware("http")(basic_log_requests)

    # Register routes (health routes don't need auth)
    app.include_router(health.router)
    
    # Legacy protected routes (keep for backward compatibility)
    app.include_router(tasks.router)
    app.include_router(cluster.router)
    app.include_router(
        model_router, 
        prefix="/api/v1",
        dependencies=[AUTH_DEPENDENCY]
    )
      # New integrated routes (CLI-compatible)
    app.include_router(api_health_router)         # /api/health (CLI compatibility)
    app.include_router(integrated_system_router)  # System routes (no auth for ping/health)
    app.include_router(integrated_model_router)   # /api/models/*
    app.include_router(integrated_task_router)    # /api/tasks/*
    app.include_router(integrated_cluster_router) # /api/workers/*
    
    # Admin management routes (protected)
    app.include_router(admin_router)              # /admin/* (management interface)

    return app


def create_enhanced_logging_middleware(api_request_service):
    """Create enhanced request logging middleware with database persistence"""
    async def enhanced_log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Start request logging
        request_id = None
        try:
            request_id = await api_request_service.start_request(
                method=request.method,
                path=request.url.path,
                query_params=dict(request.query_params),
                headers=dict(request.headers),
                client_ip=request.client.host if request.client else "unknown"
            )
        except Exception as e:
            logger.warning(f"Failed to start request logging: {e}")
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Complete request logging
            if request_id:
                try:
                    await api_request_service.complete_request(
                        request_id=request_id,
                        status_code=response.status_code,
                        response_time_ms=int(process_time * 1000)
                    )
                except Exception as e:
                    logger.warning(f"Failed to complete request logging: {e}")
            
            # Basic logging
            logger.info(
                "Request processed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=process_time,
                request_id=request_id
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error
            if request_id:
                try:
                    await api_request_service.complete_request(
                        request_id=request_id,
                        status_code=500,
                        response_time_ms=int(process_time * 1000),
                        error_message=str(e)
                    )
                except Exception as log_e:
                    logger.warning(f"Failed to complete error request logging: {log_e}")
            
            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=process_time,
                request_id=request_id
            )
            raise
    
    return enhanced_log_requests


async def basic_log_requests(request: Request, call_next):
    """Basic request logging middleware (fallback)"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        "Request processed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    return response


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
