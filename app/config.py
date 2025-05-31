"""
Gateway Manager Configuration
Uses centralized BitingLip configuration system.
"""

# Import from centralized configuration system
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../config'))

from central_config import get_config
from service_discovery import ServiceDiscovery

class GatewayManagerSettings:
    """Gateway Manager specific configuration adapter"""
    
    def __init__(self):
        self.config = get_config('gateway_manager')
        self.service_discovery = ServiceDiscovery()
    
    @property
    def host(self):
        return self.config.gateway_host
    
    @property 
    def port(self):
        return self.config.gateway_port
    
    @property
    def debug(self):
        return self.config.debug
    
    @property
    def cors_origins(self):
        return self.config.cors_origins
    
    @property
    def celery_broker_url(self):
        """Celery broker URL - default to Redis"""
        return getattr(self.config, 'celery_broker_url', 'redis://localhost:6379/0')
    
    @property
    def celery_result_backend(self):
        """Celery result backend - default to Redis"""
        return getattr(self.config, 'celery_result_backend', 'redis://localhost:6379/0')
    
    @property
    def redis_url(self):
        """Redis URL for caching and task queue"""
        return getattr(self.config, 'redis_url', 'redis://localhost:6379/0')
    
    @property 
    def celery_task_serializer(self):
        """Celery task serializer"""
        return getattr(self.config, 'celery_task_serializer', 'json')
    
    @property
    def celery_result_serializer(self):
        """Celery result serializer"""
        return getattr(self.config, 'celery_result_serializer', 'json')
    
    @property
    def celery_accept_content(self):
        """Celery accepted content types"""
        return getattr(self.config, 'celery_accept_content', ['json'])
    
    @property
    def celery_timezone(self):
        """Celery timezone"""
        return getattr(self.config, 'celery_timezone', 'UTC')
    
    @property
    def celery_enable_utc(self):
        """Celery enable UTC"""
        return getattr(self.config, 'celery_enable_utc', True)
    
    @property
    def celery_task_track_started(self):
        """Celery track task started"""
        return getattr(self.config, 'celery_task_track_started', True)

def get_settings():
    """Get gateway manager settings instance"""
    return GatewayManagerSettings()

# Create default instance
settings = get_settings()

# Backward compatibility alias
Settings = GatewayManagerSettings

# Export the same interface as before for backward compatibility
__all__ = ['Settings', 'settings', 'GatewayManagerSettings']
