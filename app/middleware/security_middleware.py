"""
Security monitoring middleware for Gateway Manager
"""

import time
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.models import SecurityService

logger = structlog.get_logger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security monitoring and threat detection"""
    
    def __init__(self, app, security_service: SecurityService):
        super().__init__(app)
        self.security_service = security_service
        
        # Security patterns to monitor
        self.suspicious_patterns = {
            'sql_injection': [
                'union select', 'drop table', 'insert into', 'delete from',
                'update set', 'exec(', 'execute(', 'sp_executesql'
            ],
            'xss_attempt': [
                '<script', 'javascript:', 'onload=', 'onerror=',
                'onclick=', 'onmouseover=', 'alert(', 'document.cookie'
            ],
            'path_traversal': [
                '../', '..\\', '..%2f', '..%5c', '%2e%2e%2f', '%2e%2e%5c'
            ],
            'command_injection': [
                '; cat', '| cat', '& cat', '; ls', '| ls', '& ls',
                '; wget', '| wget', '& wget', '; curl', '| curl'
            ]
        }
        
        # Blocked user agents (known bots/scanners)
        self.blocked_user_agents = [
            'nikto', 'sqlmap', 'nmap', 'masscan', 'nessus',
            'burpsuite', 'w3af', 'skipfish', 'gobuster'
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Store request start time
        request.state.start_time = time.time()
        
        # Perform security checks
        await self._check_security_threats(request)
        
        # Process request
        response = await call_next(request)
        
        # Post-processing security checks
        await self._post_process_security(request, response)
        
        return response
    
    async def _check_security_threats(self, request: Request) -> None:
        """Check for various security threats in the request"""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "").lower()
        path = str(request.url.path).lower()
        query_string = str(request.url.query).lower()
        
        # Check for blocked user agents
        if any(blocked in user_agent for blocked in self.blocked_user_agents):
            await self.security_service.create_incident(
                incident_type="suspicious_activity",
                severity="high",
                source_ip=client_ip,
                description=f"Blocked user agent detected: {user_agent}",
                details={
                    "user_agent": user_agent,
                    "path": path,
                    "detection_type": "blocked_user_agent"
                },
                user_agent=request.headers.get("user-agent"),
                request_path=request.url.path,
                request_method=request.method
            )
        
        # Check for suspicious patterns in path and query
        full_request = f"{path} {query_string}"
        
        for attack_type, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                if pattern in full_request:
                    await self.security_service.create_incident(
                        incident_type="suspicious_activity",
                        severity="high" if attack_type in ['sql_injection', 'command_injection'] else "medium",
                        source_ip=client_ip,
                        description=f"Potential {attack_type} attempt detected",
                        details={
                            "attack_type": attack_type,
                            "detected_pattern": pattern,
                            "path": path,
                            "query_string": query_string,
                            "user_agent": user_agent
                        },
                        user_agent=request.headers.get("user-agent"),
                        request_path=request.url.path,
                        request_method=request.method
                    )
                    break  # Only log first match per attack type
        
        # Check for general suspicious activity
        await self.security_service.check_suspicious_activity(
            source_ip=client_ip,
            request_path=request.url.path,
            user_agent=request.headers.get("user-agent")
        )
    
    async def _post_process_security(self, request: Request, response) -> None:
        """Post-process security checks after request completion"""
        processing_time = time.time() - request.state.start_time
        
        # Check for unusually slow responses (potential DoS)
        if processing_time > 30.0:  # 30 seconds
            client_ip = self._get_client_ip(request)
            
            await self.security_service.create_incident(
                incident_type="suspicious_activity",
                severity="medium",
                source_ip=client_ip,
                description=f"Unusually slow request detected: {processing_time:.2f}s",
                details={
                    "processing_time": processing_time,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "detection_type": "slow_request"
                },
                user_agent=request.headers.get("user-agent"),
                request_path=request.url.path,
                request_method=request.method
            )
        
        # Check for error responses that might indicate probing
        if response.status_code >= 400:
            await self._check_error_patterns(request, response)
    
    async def _check_error_patterns(self, request: Request, response) -> None:
        """Check for error response patterns that might indicate attacks"""
        client_ip = self._get_client_ip(request)
        
        # Check for specific error codes that might indicate attacks
        suspicious_errors = {
            401: "unauthorized_access_attempt", 
            403: "forbidden_access_attempt",
            404: "resource_probing",
            405: "method_probing",
            500: "server_error_trigger"
        }
        
        error_type = suspicious_errors.get(response.status_code)
        if error_type:
            # Count recent errors from this IP
            # This would typically check a cache or recent database records
            # For now, we'll create an incident for high-value error codes
            
            if response.status_code in [401, 403, 500]:
                await self.security_service.create_incident(
                    incident_type="suspicious_activity",
                    severity="medium",
                    source_ip=client_ip,
                    description=f"Repeated {error_type} from same IP",
                    details={
                        "error_type": error_type,
                        "status_code": response.status_code,
                        "path": request.url.path,
                        "method": request.method,
                        "detection_type": "error_pattern"
                    },
                    user_agent=request.headers.get("user-agent"),
                    request_path=request.url.path,
                    request_method=request.method
                )
    
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
