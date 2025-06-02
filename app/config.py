"""
Gateway Manager Configuration
Uses the new distributed configuration system for microservice independence.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path to access config package
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import from the config package (avoid circular imports)
from config.distributed_config import load_service_config, load_infrastructure_config
from config.service_discovery import ServiceDiscovery

class GatewayManagerSettings:
    """Gateway Manager specific configuration adapter using distributed config"""
    
    def __init__(self):
        # Load service-specific configuration
        self.config = load_service_config('gateway-manager', 'manager')
        
        # Load infrastructure configuration for shared resources
        self.infrastructure = load_infrastructure_config()
        
        # Initialize service discovery
        try:
            self.service_discovery = ServiceDiscovery()
        except Exception as e:
            print(f"Warning: Could not initialize service discovery: {e}")
            self.service_discovery = None
    
    def get_config_value(self, key: str, default: str = '') -> str:
        """Get configuration value with fallback to environment variables"""
        return self.config.get(key, os.getenv(key, default))
    
    @property
    def host(self):
        return self.get_config_value('GATEWAY_HOST', 'localhost')
    
    @property 
    def port(self):
        return int(self.get_config_value('GATEWAY_PORT', '8000'))
    
    @property
    def debug(self):
        return self.get_config_value('DEBUG', 'true').lower() == 'true'
    
    @property
    def cors_origins(self):
        origins = self.get_config_value('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173')
        return [origin.strip() for origin in origins.split(',')]
    
    @property
    def celery_broker_url(self):
        """Celery broker URL - default to Redis"""
        return self.get_config_value('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    
    @property
    def celery_result_backend(self):
        """Celery result backend - default to Redis"""
        return self.get_config_value('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    @property
    def redis_url(self):
        """Redis URL for caching and task queue"""
        return self.get_config_value('REDIS_URL', 'redis://localhost:6379/0')
    
    @property 
    def celery_task_serializer(self):
        """Celery task serializer"""
        return self.get_config_value('CELERY_TASK_SERIALIZER', 'json')
    
    @property
    def celery_result_serializer(self):
        """Celery result serializer"""
        return self.get_config_value('CELERY_RESULT_SERIALIZER', 'json')
    
    @property
    def celery_accept_content(self):
        """Celery accepted content types"""
        content = self.get_config_value('CELERY_ACCEPT_CONTENT', 'json')
        return [content] if isinstance(content, str) else content
    
    @property
    def celery_timezone(self):
        """Celery timezone"""
        return self.get_config_value('CELERY_TIMEZONE', 'UTC')
    
    @property
    def celery_enable_utc(self):
        """Celery enable UTC"""
        return self.get_config_value('CELERY_ENABLE_UTC', 'true').lower() == 'true'
    
    @property
    def celery_task_track_started(self):
        """Celery track task started"""
        return self.get_config_value('CELERY_TASK_TRACK_STARTED', 'true').lower() == 'true'
    
    @property
    def rate_limit_per_minute(self):
        return int(self.get_config_value('RATE_LIMIT_PER_MINUTE', '100'))
    
    @property
    def max_request_size_mb(self):
        return int(self.get_config_value('MAX_REQUEST_SIZE_MB', '10'))
    
    @property
    def db_host(self):
        return self.get_config_value('GATEWAY_DB_HOST', 'localhost')
    
    @property
    def db_port(self):
        return int(self.get_config_value('GATEWAY_DB_PORT', '5432'))
    
    @property
    def db_name(self):
        return self.get_config_value('GATEWAY_DB_NAME', 'bitinglip_gateway')
    
    @property
    def db_user(self):
        return self.get_config_value('GATEWAY_DB_USER', 'bitinglip')
    
    @property
    def db_password(self):
        return self.get_config_value('GATEWAY_DB_PASSWORD', 'secure_password')
    
    @property
    def log_level(self):
        return self.get_config_value('LOG_LEVEL', 'INFO')
    
    @property
    def log_format(self):
        """Log format (json or console)"""
        return self.get_config_value('LOG_FORMAT', 'console')
    
    # Security Configuration
    @property
    def jwt_secret_key(self):
        """JWT secret key for token signing"""
        return self.get_config_value('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
    
    @property
    def jwt_algorithm(self):
        """JWT algorithm for token signing"""
        return self.get_config_value('JWT_ALGORITHM', 'HS256')
    
    @property
    def api_key_header(self):
        """API key header name"""
        return self.get_config_value('API_KEY_HEADER', 'X-API-Key')
    
    @property
    def api_key(self):
        """API key for authentication (legacy support)"""
        return self.get_config_value('API_KEY', '')
    
    # Rate Limiting Configuration
    @property
    def default_rate_limit_per_minute(self):
        """Default rate limit per minute for IP addresses"""
        return int(self.get_config_value('DEFAULT_RATE_LIMIT_PER_MINUTE', '60'))
    
    @property
    def default_rate_limit_per_hour(self):
        """Default rate limit per hour for IP addresses"""
        return int(self.get_config_value('DEFAULT_RATE_LIMIT_PER_HOUR', '1000'))
    
    @property
    def authenticated_rate_limit_per_minute(self):
        """Rate limit per minute for authenticated users"""
        return int(self.get_config_value('AUTHENTICATED_RATE_LIMIT_PER_MINUTE', '300'))
    
    @property
    def authenticated_rate_limit_per_hour(self):
        """Rate limit per hour for authenticated users"""
        return int(self.get_config_value('AUTHENTICATED_RATE_LIMIT_PER_HOUR', '10000'))
    
    # Security Threat Detection
    @property
    def enable_threat_detection(self):
        """Enable security threat detection middleware"""
        return self.get_config_value('ENABLE_THREAT_DETECTION', 'true').lower() == 'true'
    
    @property
    def max_failed_auth_attempts(self):
        """Maximum failed authentication attempts before blocking"""
        return int(self.get_config_value('MAX_FAILED_AUTH_ATTEMPTS', '5'))
    
    @property
    def security_block_duration_minutes(self):
        """Duration to block IP after security violations (minutes)"""
        return int(self.get_config_value('SECURITY_BLOCK_DURATION_MINUTES', '60'))
    
    @property
    def max_request_body_size(self):
        """Maximum request body size in bytes"""
        return int(self.get_config_value('MAX_REQUEST_BODY_SIZE', '10485760'))  # 10MB
    
    # Database Connection Pool Settings
    @property
    def db_pool_min_size(self):
        """Minimum database connection pool size"""
        return int(self.get_config_value('DB_POOL_MIN_SIZE', '5'))
    
    @property
    def db_pool_max_size(self):
        """Maximum database connection pool size"""
        return int(self.get_config_value('DB_POOL_MAX_SIZE', '20'))
    
    @property
    def db_pool_max_queries(self):
        """Maximum queries per connection before recycling"""
        return int(self.get_config_value('DB_POOL_MAX_QUERIES', '50000'))
    
    @property
    def db_pool_max_inactive_time(self):
        """Maximum inactive time for connections (seconds)"""
        return int(self.get_config_value('DB_POOL_MAX_INACTIVE_TIME', '3600'))
    
    # Data Retention Settings
    @property
    def api_request_retention_days(self):
        """Days to retain API request logs"""
        return int(self.get_config_value('API_REQUEST_RETENTION_DAYS', '30'))
    
    @property
    def security_incident_retention_days(self):
        """Days to retain security incident logs"""
        return int(self.get_config_value('SECURITY_INCIDENT_RETENTION_DAYS', '90'))
    
    @property
    def rate_limit_cleanup_interval_hours(self):
        """Hours between rate limit bucket cleanup"""
        return int(self.get_config_value('RATE_LIMIT_CLEANUP_INTERVAL_HOURS', '24'))
    
    # Prometheus and Monitoring
    @property
    def enable_prometheus(self):
        """Enable Prometheus metrics server"""
        return self.get_config_value('ENABLE_PROMETHEUS', 'false').lower() == 'true'
    
    @property
    def prometheus_port(self):
        """Prometheus metrics server port"""
        return int(self.get_config_value('PROMETHEUS_PORT', '8001'))
    
    # Celery Task Configuration  
    @property
    def task_soft_time_limit(self):
        """Celery task soft time limit (seconds)"""
        return int(self.get_config_value('CELERY_TASK_SOFT_TIME_LIMIT', '600'))
    
    @property
    def task_time_limit(self):
        """Celery task hard time limit (seconds)"""
        return int(self.get_config_value('CELERY_TASK_TIME_LIMIT', '900'))
    
    @property
    def task_max_retries(self):
        """Maximum number of task retries"""
        return int(self.get_config_value('CELERY_TASK_MAX_RETRIES', '3'))
    
    @property
    def task_default_retry_delay(self):
        """Default retry delay for failed tasks (seconds)"""
        return int(self.get_config_value('CELERY_TASK_RETRY_DELAY', '60'))
    
    @property
    def result_expires(self):
        """Task result expiration time (seconds)"""
        return int(self.get_config_value('CELERY_RESULT_EXPIRES', '3600'))
    
    # Service Discovery URLs
    @property
    def model_manager_url(self):
        """Model Manager service URL"""
        return self.get_config_value('MODEL_MANAGER_URL', 'http://localhost:8001')
    
    @property
    def task_manager_url(self):
        """Task Manager service URL"""
        return self.get_config_value('TASK_MANAGER_URL', 'http://localhost:8002')
    
    @property
    def cluster_manager_url(self):
        """Cluster Manager service URL"""
        return self.get_config_value('CLUSTER_MANAGER_URL', 'http://localhost:8003')
    
    @property 
    def worker_manager_url(self):
        """Worker Manager service URL"""
        return self.get_config_value('WORKER_MANAGER_URL', 'http://localhost:8004')

def get_settings():
    """Get gateway manager settings instance"""
    return GatewayManagerSettings()

# Create default instance
settings = get_settings()

# Backward compatibility alias
Settings = GatewayManagerSettings

# Export the same interface as before for backward compatibility
__all__ = ['Settings', 'settings', 'GatewayManagerSettings']
