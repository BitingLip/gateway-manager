-- Gateway Manager Database Schema
-- PostgreSQL schema for API gateway logs and rate limiting

-- API request logging
CREATE TABLE IF NOT EXISTS api_requests (
    id SERIAL PRIMARY KEY,
    request_id TEXT UNIQUE NOT NULL,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    query_params JSONB DEFAULT '{}'::jsonb,
    headers JSONB DEFAULT '{}'::jsonb,
    body_size INTEGER,
    client_ip INET,
    user_agent TEXT,
    auth_user TEXT,
    service_name TEXT,
    endpoint TEXT,
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_status INTEGER,
    response_size INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Rate limiting buckets
CREATE TABLE IF NOT EXISTS rate_limit_buckets (
    id SERIAL PRIMARY KEY,
    bucket_key TEXT NOT NULL, -- combination of IP, user, endpoint etc.
    bucket_type TEXT NOT NULL, -- 'ip', 'user', 'endpoint', 'service'
    window_start TIMESTAMP NOT NULL,
    window_duration INTEGER NOT NULL, -- seconds
    request_count INTEGER DEFAULT 0,
    max_requests INTEGER NOT NULL,
    last_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reset_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(bucket_key, window_start)
);

-- API endpoint configuration
CREATE TABLE IF NOT EXISTS api_endpoints (
    id SERIAL PRIMARY KEY,
    service_name TEXT NOT NULL,
    method TEXT NOT NULL,
    path_pattern TEXT NOT NULL,
    rate_limit_rpm INTEGER, -- requests per minute
    rate_limit_rps INTEGER, -- requests per second
    auth_required BOOLEAN DEFAULT true,
    enabled BOOLEAN DEFAULT true,
    timeout_seconds INTEGER DEFAULT 30,
    retry_attempts INTEGER DEFAULT 3,
    circuit_breaker_enabled BOOLEAN DEFAULT true,
    circuit_breaker_threshold INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(service_name, method, path_pattern)
);

-- Circuit breaker state tracking
CREATE TABLE IF NOT EXISTS circuit_breaker_state (
    id SERIAL PRIMARY KEY,
    service_name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'closed', -- 'closed', 'open', 'half-open'
    failure_count INTEGER DEFAULT 0,
    last_failure TIMESTAMP,
    next_attempt TIMESTAMP,
    state_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(service_name, endpoint)
);

-- Service health monitoring
CREATE TABLE IF NOT EXISTS service_health (
    id SERIAL PRIMARY KEY,
    service_name TEXT NOT NULL,
    health_check_url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unknown', -- 'healthy', 'unhealthy', 'unknown'
    response_time_ms INTEGER,
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_success TIMESTAMP,
    last_failure TIMESTAMP,
    consecutive_failures INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(service_name)
);

-- API authentication and authorization logs
CREATE TABLE IF NOT EXISTS auth_events (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL, -- 'login', 'logout', 'token_refresh', 'permission_check'
    user_id TEXT,
    username TEXT,
    client_ip INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    token_type TEXT, -- 'jwt', 'api_key', 'oauth'
    permissions_checked JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Security incident tracking
CREATE TABLE IF NOT EXISTS security_incidents (
    id SERIAL PRIMARY KEY,
    incident_type TEXT NOT NULL, -- 'rate_limit_exceeded', 'auth_failure', 'suspicious_activity'
    severity TEXT NOT NULL DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'
    source_ip INET,
    user_id TEXT,
    description TEXT NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by TEXT,
    action_taken TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_api_requests_timestamp ON api_requests(request_timestamp);
CREATE INDEX IF NOT EXISTS idx_api_requests_path ON api_requests(path);
CREATE INDEX IF NOT EXISTS idx_api_requests_service ON api_requests(service_name);
CREATE INDEX IF NOT EXISTS idx_api_requests_status ON api_requests(response_status);
CREATE INDEX IF NOT EXISTS idx_api_requests_client_ip ON api_requests(client_ip);
CREATE INDEX IF NOT EXISTS idx_api_requests_user ON api_requests(auth_user);

CREATE INDEX IF NOT EXISTS idx_rate_limit_bucket_key ON rate_limit_buckets(bucket_key);
CREATE INDEX IF NOT EXISTS idx_rate_limit_window_start ON rate_limit_buckets(window_start);
CREATE INDEX IF NOT EXISTS idx_rate_limit_reset_at ON rate_limit_buckets(reset_at);

CREATE INDEX IF NOT EXISTS idx_api_endpoints_service ON api_endpoints(service_name);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_enabled ON api_endpoints(enabled);

CREATE INDEX IF NOT EXISTS idx_circuit_breaker_service ON circuit_breaker_state(service_name);
CREATE INDEX IF NOT EXISTS idx_circuit_breaker_state ON circuit_breaker_state(state);

CREATE INDEX IF NOT EXISTS idx_service_health_name ON service_health(service_name);
CREATE INDEX IF NOT EXISTS idx_service_health_status ON service_health(status);
CREATE INDEX IF NOT EXISTS idx_service_health_last_check ON service_health(last_check);

CREATE INDEX IF NOT EXISTS idx_auth_events_timestamp ON auth_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_auth_events_user_id ON auth_events(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_events_client_ip ON auth_events(client_ip);
CREATE INDEX IF NOT EXISTS idx_auth_events_success ON auth_events(success);

CREATE INDEX IF NOT EXISTS idx_security_incidents_detected_at ON security_incidents(detected_at);
CREATE INDEX IF NOT EXISTS idx_security_incidents_severity ON security_incidents(severity);
CREATE INDEX IF NOT EXISTS idx_security_incidents_source_ip ON security_incidents(source_ip);

-- JSONB indexes for metadata searches
CREATE INDEX IF NOT EXISTS idx_api_requests_metadata ON api_requests USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_rate_limit_metadata ON rate_limit_buckets USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_auth_events_metadata ON auth_events USING GIN(metadata);

-- Performance statistics view
CREATE OR REPLACE VIEW api_performance_stats AS
SELECT 
    service_name,
    method,
    path,
    DATE_TRUNC('hour', request_timestamp) as hour,
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE response_status < 400) as successful_requests,
    COUNT(*) FILTER (WHERE response_status >= 400 AND response_status < 500) as client_errors,
    COUNT(*) FILTER (WHERE response_status >= 500) as server_errors,
    AVG(response_time_ms) as avg_response_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time,
    MAX(response_time_ms) as max_response_time
FROM api_requests
WHERE request_timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY service_name, method, path, DATE_TRUNC('hour', request_timestamp)
ORDER BY hour DESC, total_requests DESC;

-- Rate limiting cleanup function
CREATE OR REPLACE FUNCTION cleanup_old_rate_limit_buckets()
RETURNS void AS $$
BEGIN
    DELETE FROM rate_limit_buckets 
    WHERE reset_at < NOW() - INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;

-- Security alerts view
CREATE OR REPLACE VIEW security_alerts AS
SELECT 
    incident_type,
    severity,
    source_ip,
    COUNT(*) as incident_count,
    MAX(detected_at) as last_incident,
    MIN(detected_at) as first_incident
FROM security_incidents
WHERE detected_at >= NOW() - INTERVAL '24 hours'
  AND resolved_at IS NULL
GROUP BY incident_type, severity, source_ip
ORDER BY severity DESC, incident_count DESC;
