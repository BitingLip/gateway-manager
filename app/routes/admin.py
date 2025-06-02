"""
Management API routes for Gateway Manager
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
import structlog

from app.models import (
    AuthenticationService, APIRequestService, RateLimitService, 
    SecurityService, get_db, DatabaseManager
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# Pydantic models for API requests/responses
class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., description="Name for the API key")
    description: Optional[str] = Field(None, description="Description of the API key")
    permissions: Optional[List[str]] = Field(default=[], description="List of permissions")
    rate_limit: Optional[int] = Field(None, description="Custom rate limit (requests per hour)")
    expires_in_days: Optional[int] = Field(None, description="Expiration in days")


class APIKeyResponse(BaseModel):
    key_id: str
    api_key: str
    name: str
    description: Optional[str]
    rate_limit: Optional[int]
    permissions: List[str]
    expires_at: Optional[datetime]


class RateLimitUpdateRequest(BaseModel):
    bucket_type: str = Field(..., description="Type of bucket (ip, api_key, user)")
    identifier: str = Field(..., description="Identifier for the bucket")
    max_requests: int = Field(..., description="Maximum requests allowed")
    window_duration: int = Field(..., description="Time window in seconds")


class SecurityIncidentResponse(BaseModel):
    incident_id: str
    incident_type: str
    severity: str
    source_ip: str
    description: str
    is_resolved: bool
    created_at: datetime


class BlockIPRequest(BaseModel):
    ip_address: str = Field(..., description="IP address to block")
    reason: str = Field(..., description="Reason for blocking")
    duration_hours: Optional[int] = Field(None, description="Block duration in hours")


class UnblockIPRequest(BaseModel):
    ip_address: str = Field(..., description="IP address to unblock")
    reason: str = Field(..., description="Reason for unblocking")


# Dependency to get services
async def get_auth_service(db: DatabaseManager = Depends(get_db)) -> AuthenticationService:
    return AuthenticationService(db)


async def get_api_request_service(db: DatabaseManager = Depends(get_db)) -> APIRequestService:
    return APIRequestService(db)


async def get_rate_limit_service(db: DatabaseManager = Depends(get_db)) -> RateLimitService:
    return RateLimitService(db)


async def get_security_service(db: DatabaseManager = Depends(get_db)) -> SecurityService:
    return SecurityService(db)


# API Key Management Routes
@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Create a new API key"""
    try:
        key_id, api_key = await auth_service.create_api_key(
            name=request.name,
            description=request.description,
            permissions=request.permissions,
            rate_limit=request.rate_limit,
            expires_in_days=request.expires_in_days,
            created_by="admin"  # TODO: Get from authenticated user
        )
        
        return APIKeyResponse(
            key_id=key_id,
            api_key=api_key,
            name=request.name,
            description=request.description,
            rate_limit=request.rate_limit,
            permissions=request.permissions or [],
            expires_at=datetime.utcnow() + timedelta(days=request.expires_in_days) if request.expires_in_days else None
        )
        
    except Exception as e:
        logger.error("Failed to create API key", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.get("/api-keys")
async def list_api_keys(
    include_inactive: bool = Query(False, description="Include inactive keys"),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """List all API keys"""
    try:
        keys = await auth_service.get_api_keys(include_inactive=include_inactive)
        return {"api_keys": keys}
        
    except Exception as e:
        logger.error("Failed to list API keys", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Revoke an API key"""
    try:
        success = await auth_service.revoke_api_key(
            key_id=key_id,
            revoked_by="admin"  # TODO: Get from authenticated user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
            
        return {"message": "API key revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to revoke API key", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )


@router.get("/api-keys/{key_id}")
async def get_api_key(
    key_id: str,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Get details of a specific API key"""
    try:
        key_info = await auth_service.get_api_key_info(key_id)
        
        if not key_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
            
        return key_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get API key", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,            detail="Failed to get API key"
        )


# Rate Limiting Management Routes
@router.get("/rate-limits")
async def get_rate_limits(
    bucket_type: Optional[str] = Query(None, description="Filter by bucket type"),
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service)
):
    """Get rate limit information"""
    try:
        limits = await rate_limit_service.get_rate_limits(bucket_type=bucket_type)
        return {"rate_limits": limits}
        
    except Exception as e:
        logger.error("Failed to get rate limits", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rate limits"
        )


@router.put("/rate-limits")
async def update_rate_limit(
    request: RateLimitUpdateRequest,
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service)
):
    """Update rate limit for a bucket"""
    try:
        success = await rate_limit_service.update_rate_limit(
            bucket_type=request.bucket_type,
            identifier=request.identifier,
            max_requests=request.max_requests,
            window_duration=request.window_duration
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rate limit bucket not found"
            )
            
        return {"message": "Rate limit updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update rate limit", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update rate limit"
        )


@router.delete("/rate-limits/{bucket_type}/{identifier}")
async def reset_rate_limit(
    bucket_type: str,
    identifier: str,
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service)
):
    """Reset rate limit for a specific bucket"""
    try:
        success = await rate_limit_service.reset_rate_limit(
            bucket_type=bucket_type,
            identifier=identifier
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rate limit bucket not found"
            )
            
        return {"message": "Rate limit reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to reset rate limit", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset rate limit"
        )


# Security Management Routes
@router.get("/security/incidents")
async def list_security_incidents(
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, description="Maximum number of incidents to return"),
    security_service: SecurityService = Depends(get_security_service)
):
    """List security incidents"""
    try:
        incidents = await security_service.get_security_incidents(
            resolved=resolved,
            severity=severity,
            limit=limit
        )
        return {"incidents": incidents}
        
    except Exception as e:
        logger.error("Failed to list security incidents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list security incidents"
        )


@router.put("/security/incidents/{incident_id}/resolve")
async def resolve_security_incident(
    incident_id: str,
    security_service: SecurityService = Depends(get_security_service)
):
    """Mark a security incident as resolved"""
    try:
        success = await security_service.resolve_incident(
            incident_id=incident_id,
            resolved_by="admin"  # TODO: Get from authenticated user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Security incident not found"
            )
            
        return {"message": "Security incident resolved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to resolve security incident", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve security incident"
        )


@router.post("/security/block-ip")
async def block_ip_address(
    request: BlockIPRequest,
    security_service: SecurityService = Depends(get_security_service)
):
    """Block an IP address"""
    try:
        success = await security_service.block_ip(
            ip_address=request.ip_address,
            reason=request.reason,
            duration_hours=request.duration_hours,
            blocked_by="admin"  # TODO: Get from authenticated user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to block IP address"
            )
            
        return {"message": f"IP address {request.ip_address} blocked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to block IP address", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block IP address"
        )


@router.delete("/security/block-ip")
async def unblock_ip_address(
    request: UnblockIPRequest,
    security_service: SecurityService = Depends(get_security_service)
):
    """Unblock an IP address"""
    try:
        success = await security_service.unblock_ip(
            ip_address=request.ip_address,
            unblocked_by="admin"  # TODO: Get from authenticated user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="IP address not found in blocklist"
            )
            
        return {"message": f"IP address {request.ip_address} unblocked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to unblock IP address", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unblock IP address"
        )


# Analytics and Monitoring Routes
@router.get("/analytics/requests")
async def get_request_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    group_by: str = Query("hour", description="Group by: hour, day, week"),
    api_request_service: APIRequestService = Depends(get_api_request_service)
):
    """Get request analytics"""
    try:
        analytics = await api_request_service.get_request_analytics(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        return {"analytics": analytics}
        
    except Exception as e:
        logger.error("Failed to get request analytics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get request analytics"
        )


@router.get("/health")
async def admin_health_check():
    """Health check endpoint for admin API"""
    try:
        # Get basic health status
        health_status = "healthy"
        
        # In a full implementation, you would check:
        # - Database connectivity
        # - Service dependencies
        # - Resource usage
        # - Error rates
        
        return {
            "status": health_status,
            "timestamp": datetime.utcnow(),
            "service": "gateway-manager-admin"
        }
        
    except Exception as e:
        logger.error("Failed to get system health", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow(),
            "error": "Failed to retrieve health metrics"
        }
