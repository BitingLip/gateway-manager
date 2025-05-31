# Gateway Manager Deployment Guide

## Overview

This guide covers deployment strategies for the Gateway Manager in both development and production environments. The Gateway Manager serves as the primary API interface for the BitingLip AI inference cluster.

## Development Deployment

### Local Development Setup

1. **Prerequisites:**
   ```bash
   # Install Python 3.10+
   python --version
   
   # Install Redis
   # Ubuntu/Debian:
   sudo apt install redis-server
   # macOS:
   brew install redis
   # Windows:
   # Download from https://redis.io/download
   
   # Install PostgreSQL (optional, for persistent storage)
   # Ubuntu/Debian:
   sudo apt install postgresql postgresql-contrib
   # macOS:
   brew install postgresql
   ```

2. **Quick Start:**
   ```bash
   cd gateway-manager
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # .\venv\Scripts\activate  # Windows
   
   pip install -r requirements.txt
   cp .env.example .env
   
   # Edit .env with your configuration
   # Set CLUSTER_MANAGER_URL, MODEL_MANAGER_URL, etc.
   
   # Start Redis
   redis-server
   
   # Run database migrations (if using PostgreSQL)
   alembic upgrade head
   
   # Start the API server
   python start_server.py
   ```

3. **Verify Installation:**
   ```bash
   # Check API health
   curl http://localhost:8080/health
   
   # View API documentation
   open http://localhost:8080/docs
   
   # Test authentication
   curl -H "Authorization: Bearer test-api-key" \
        http://localhost:8080/api/v1/cluster/status
   ```

### Development with Docker

1. **Create `docker-compose.dev.yml`:**
   ```yaml
   version: '3.8'
   
   services:
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data
   
     postgres:
       image: postgres:15-alpine
       environment:
         POSTGRES_DB: gateway
         POSTGRES_USER: gateway
         POSTGRES_PASSWORD: development
       ports:
         - "5432:5432"
       volumes:
         - postgres_data:/var/lib/postgresql/data
   
     gateway-manager:
       build:
         context: .
         dockerfile: Dockerfile.dev
       ports:
         - "8080:8080"
       environment:
         - REDIS_URL=redis://redis:6379/0
         - DATABASE_URL=postgresql://gateway:development@postgres/gateway
         - DEBUG=true
         - LOG_LEVEL=DEBUG
       volumes:
         - .:/app
       depends_on:
         - redis
         - postgres
       command: uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   
   volumes:
     redis_data:
     postgres_data:
   ```

2. **Start development environment:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

## Production Deployment

### Architecture Options

#### Option 1: Single Node Deployment
Best for small deployments or testing.

```mermaid
graph TB
    subgraph "Single Node"
        LB[Load Balancer<br/>Nginx/HAProxy]
        API[Gateway Manager]
        Redis[Redis Cache]
        DB[PostgreSQL]
    end
    
    Client -->|HTTPS| LB
    LB -->|HTTP| API
    API --> Redis
    API --> DB
```

#### Option 2: Multi-Node High Availability
Recommended for production environments.

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        LB1[Load Balancer 1]
        LB2[Load Balancer 2]
    end
    
    subgraph "API Layer"
        API1[Gateway Manager 1]
        API2[Gateway Manager 2]
        API3[Gateway Manager 3]
    end
    
    subgraph "Data Layer"
        Redis1[(Redis Primary)]
        Redis2[(Redis Replica)]
        PG1[(PostgreSQL Primary)]
        PG2[(PostgreSQL Replica)]
    end
    
    Client --> LB1
    Client --> LB2
    LB1 --> API1
    LB1 --> API2
    LB2 --> API2
    LB2 --> API3
    
    API1 --> Redis1
    API2 --> Redis1
    API3 --> Redis1
    Redis1 --> Redis2
    
    API1 --> PG1
    API2 --> PG1
    API3 --> PG1
    PG1 --> PG2
```

### Production Docker Setup

1. **Production Dockerfile:**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       libpq-dev \
       curl \
       && rm -rf /var/lib/apt/lists/*
   
   # Copy requirements and install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application code
   COPY app/ ./app/
   COPY alembic/ ./alembic/
   COPY alembic.ini .
   
   # Create non-root user
   RUN useradd --create-home --shell /bin/bash app && \
       chown -R app:app /app
   USER app
   
   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
       CMD curl -f http://localhost:8080/health || exit 1
   
   EXPOSE 8080
   
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

2. **Production Docker Compose:**
   ```yaml
   version: '3.8'
   
   services:
     redis:
       image: redis:7-alpine
       restart: unless-stopped
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data
         - ./redis.conf:/usr/local/etc/redis/redis.conf
       command: redis-server /usr/local/etc/redis/redis.conf
       healthcheck:
         test: ["CMD", "redis-cli", "ping"]
         interval: 10s
         timeout: 5s
         retries: 3
   
     postgres:
       image: postgres:15-alpine
       restart: unless-stopped
       environment:
         POSTGRES_DB: gateway
         POSTGRES_USER: gateway
         POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
       ports:
         - "5432:5432"
       volumes:
         - postgres_data:/var/lib/postgresql/data
         - ./init.sql:/docker-entrypoint-initdb.d/init.sql
       secrets:
         - postgres_password
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U gateway"]
         interval: 10s
         timeout: 5s
         retries: 3
   
     gateway-manager:
       build:
         context: .
         dockerfile: Dockerfile
       restart: unless-stopped
       ports:
         - "8080:8080"
       environment:
         - REDIS_URL=redis://redis:6379/0
         - DATABASE_URL=postgresql://gateway:${POSTGRES_PASSWORD}@postgres/gateway
         - LOG_LEVEL=INFO
       env_file:
         - .env.production
       depends_on:
         redis:
           condition: service_healthy
         postgres:
           condition: service_healthy
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
         interval: 30s
         timeout: 10s
         retries: 3
       deploy:
         replicas: 2
   
     nginx:
       image: nginx:alpine
       restart: unless-stopped
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
         - ./ssl:/etc/nginx/ssl
         - ./static:/var/www/static
       depends_on:
         - gateway-manager
   
   volumes:
     redis_data:
     postgres_data:
   
   secrets:
     postgres_password:
       file: ./secrets/postgres_password.txt
   ```

### Kubernetes Deployment

1. **Namespace and ConfigMap:**
   ```yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: biting-lip
   
   ---
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: gateway-config
     namespace: biting-lip
   data:
     REDIS_URL: "redis://redis-service:6379/0"
     DATABASE_URL: "postgresql://gateway:password@postgres-service/gateway"
     LOG_LEVEL: "INFO"
     API_HOST: "0.0.0.0"
     CLUSTER_MANAGER_URL: "http://cluster-manager-service:8000"
     MODEL_MANAGER_URL: "http://model-manager-service:8001"
   ```

2. **Database Deployment:**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: postgres
     namespace: biting-lip
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: postgres
     template:
       metadata:
         labels:
           app: postgres
       spec:
         containers:
         - name: postgres
           image: postgres:15-alpine
           env:
           - name: POSTGRES_DB
             value: "gateway"
           - name: POSTGRES_USER
             value: "gateway"
           - name: POSTGRES_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: postgres-secret
                 key: password
           ports:
           - containerPort: 5432
           volumeMounts:
           - name: postgres-storage
             mountPath: /var/lib/postgresql/data
         volumes:
         - name: postgres-storage
           persistentVolumeClaim:
             claimName: postgres-pvc
   
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: postgres-service
     namespace: biting-lip
   spec:
     selector:
       app: postgres
     ports:
     - port: 5432
       targetPort: 5432
   ```

3. **Gateway Manager Deployment:**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: gateway-manager
     namespace: biting-lip
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: gateway-manager
     template:
       metadata:
         labels:
           app: gateway-manager
       spec:
         containers:
         - name: gateway-manager
           image: bitinglip/gateway-manager:latest
           ports:
           - containerPort: 8080
           envFrom:
           - configMapRef:
               name: gateway-config
           env:
           - name: SECRET_KEY
             valueFrom:
               secretKeyRef:
                 name: gateway-secrets
                 key: secret-key
           resources:
             requests:
               memory: "512Mi"
               cpu: "250m"
             limits:
               memory: "1Gi"
               cpu: "500m"
           livenessProbe:
             httpGet:
               path: /health
               port: 8080
             initialDelaySeconds: 30
             periodSeconds: 10
           readinessProbe:
             httpGet:
               path: /health
               port: 8080
             initialDelaySeconds: 5
             periodSeconds: 5
   
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: gateway-service
     namespace: biting-lip
   spec:
     selector:
       app: gateway-manager
     ports:
     - port: 80
       targetPort: 8080
     type: LoadBalancer
   ```

4. **Ingress Configuration:**
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: gateway-ingress
     namespace: biting-lip
     annotations:
       nginx.ingress.kubernetes.io/rewrite-target: /
       nginx.ingress.kubernetes.io/ssl-redirect: "true"
       nginx.ingress.kubernetes.io/rate-limit: "100"
       nginx.ingress.kubernetes.io/rate-limit-window: "1m"
   spec:
     tls:
     - hosts:
       - api.bitinglip.com
       secretName: tls-secret
     rules:
     - host: api.bitinglip.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: gateway-service
               port:
                 number: 80
   ```

## Configuration Management

### Environment Variables

#### Development (.env.development)
```bash
# API Configuration
API_HOST=localhost
API_PORT=8080
DEBUG=true

# Security
SECRET_KEY=dev-secret-key-12345
CORS_ORIGINS=["http://localhost:3000"]

# Service URLs
CLUSTER_MANAGER_URL=http://localhost:8000
MODEL_MANAGER_URL=http://localhost:8001
TASK_MANAGER_URL=http://localhost:8002

# Database
DATABASE_URL=postgresql://user:pass@localhost/gateway_dev
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# Rate Limiting
RATE_LIMIT_ENABLED=false
```

#### Production (.env.production)
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
DEBUG=false

# Security
SECRET_KEY=${SECRET_KEY}
CORS_ORIGINS=["https://app.bitinglip.com"]

# Service URLs
CLUSTER_MANAGER_URL=http://cluster-manager-service:8000
MODEL_MANAGER_URL=http://model-manager-service:8001
TASK_MANAGER_URL=http://task-manager-service:8002

# Database
DATABASE_URL=postgresql://gateway:${DB_PASSWORD}@postgres-service/gateway
REDIS_URL=redis://redis-service:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT=1000/hour

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/gateway.crt
SSL_KEY_PATH=/etc/ssl/private/gateway.key

# Performance
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
```

### Secrets Management

#### Using Docker Secrets
```yaml
services:
  gateway-manager:
    image: bitinglip/gateway-manager:latest
    secrets:
      - secret_key
      - db_password
      - api_keys
    environment:
      - SECRET_KEY_FILE=/run/secrets/secret_key
      - DB_PASSWORD_FILE=/run/secrets/db_password

secrets:
  secret_key:
    external: true
  db_password:
    external: true
  api_keys:
    external: true
```

#### Using Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gateway-secrets
  namespace: biting-lip
type: Opaque
data:
  secret-key: <base64-encoded-secret-key>
  db-password: <base64-encoded-db-password>
  jwt-secret: <base64-encoded-jwt-secret>
```

### Load Balancer Configuration

#### Nginx Configuration
```nginx
upstream gateway_backend {
    least_conn;
    server gateway-1:8080 max_fails=3 fail_timeout=30s;
    server gateway-2:8080 max_fails=3 fail_timeout=30s;
    server gateway-3:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name api.bitinglip.com;
    
    ssl_certificate /etc/ssl/certs/api.bitinglip.com.crt;
    ssl_certificate_key /etc/ssl/private/api.bitinglip.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # CORS headers
    add_header 'Access-Control-Allow-Origin' 'https://app.bitinglip.com' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
    
    location / {
        proxy_pass http://gateway_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Health check
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://gateway_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://gateway_backend/health;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.bitinglip.com;
    return 301 https://$server_name$request_uri;
}
```

## Monitoring and Observability

### Prometheus Metrics

1. **Enable metrics in FastAPI:**
   ```python
   from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
   
   # Metrics
   REQUEST_COUNT = Counter('gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
   REQUEST_DURATION = Histogram('gateway_request_duration_seconds', 'Request duration')
   ACTIVE_CONNECTIONS = Gauge('gateway_active_connections', 'Active connections')
   
   # Add metrics endpoint
   metrics_app = make_asgi_app()
   app.mount("/metrics", metrics_app)
   ```

2. **Prometheus configuration:**
   ```yaml
   scrape_configs:
     - job_name: 'gateway-manager'
       static_configs:
         - targets: ['gateway-manager:8080']
       metrics_path: /metrics
       scrape_interval: 15s
   ```

### Logging Configuration

1. **Structured logging:**
   ```python
   import structlog
   import logging
   
   # Configure structlog
   structlog.configure(
       processors=[
           structlog.stdlib.filter_by_level,
           structlog.stdlib.add_log_level,
           structlog.processors.TimeStamper(fmt="iso"),
           structlog.processors.JSONRenderer()
       ],
       context_class=dict,
       logger_factory=structlog.stdlib.LoggerFactory(),
       wrapper_class=structlog.stdlib.BoundLogger,
       cache_logger_on_first_use=True,
   )
   ```

2. **Log aggregation with ELK Stack:**
   ```yaml
   version: '3.8'
   services:
     elasticsearch:
       image: elasticsearch:8.5.0
       environment:
         - discovery.type=single-node
         - xpack.security.enabled=false
       ports:
         - "9200:9200"
   
     logstash:
       image: logstash:8.5.0
       volumes:
         - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
       depends_on:
         - elasticsearch
   
     kibana:
       image: kibana:8.5.0
       ports:
         - "5601:5601"
       depends_on:
         - elasticsearch
   
     filebeat:
       image: elastic/filebeat:8.5.0
       volumes:
         - ./filebeat.yml:/usr/share/filebeat/filebeat.yml
         - /var/log:/var/log:ro
       depends_on:
         - logstash
   ```

### Health Checks

```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "cluster_manager": await check_service("cluster-manager"),
        "model_manager": await check_service("model-manager")
    }
    
    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow(),
        "version": __version__,
        "uptime": get_uptime()
    }

async def check_service(service_name: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{service_name}:8000/health", timeout=5)
            return response.status_code == 200
    except:
        return False
```

## Security Hardening

### Network Security

1. **Firewall rules:**
   ```bash
   # Allow only necessary ports
   ufw allow 22/tcp     # SSH
   ufw allow 80/tcp     # HTTP
   ufw allow 443/tcp    # HTTPS
   ufw deny 5432/tcp    # PostgreSQL (internal only)
   ufw deny 6379/tcp    # Redis (internal only)
   ufw deny 8080/tcp    # API (behind proxy)
   ```

2. **SSL/TLS Configuration:**
   ```nginx
   # Strong SSL configuration
   ssl_protocols TLSv1.2 TLSv1.3;
   ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
   ssl_prefer_server_ciphers off;
   ssl_session_cache shared:SSL:10m;
   ssl_session_timeout 10m;
   
   # HSTS
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
   
   # Security headers
   add_header X-Frame-Options DENY always;
   add_header X-Content-Type-Options nosniff always;
   add_header X-XSS-Protection "1; mode=block" always;
   ```

### Application Security

1. **Input validation and sanitization:**
   ```python
   from pydantic import validator
   import bleach
   
   class APIRequest(BaseModel):
       prompt: str
       
       @validator('prompt')
       def sanitize_prompt(cls, v):
           # Remove potentially dangerous content
           cleaned = bleach.clean(v, tags=[], strip=True)
           return cleaned[:10000]  # Limit length
   ```

2. **API key management:**
   ```python
   from cryptography.fernet import Fernet
   
   def encrypt_api_key(api_key: str, key: bytes) -> str:
       f = Fernet(key)
       encrypted = f.encrypt(api_key.encode())
       return encrypted.decode()
   
   def decrypt_api_key(encrypted_key: str, key: bytes) -> str:
       f = Fernet(key)
       decrypted = f.decrypt(encrypted_key.encode())
       return decrypted.decode()
   ```

## Backup and Recovery

### Database Backup

1. **Automated backup script:**
   ```bash
   #!/bin/bash
   BACKUP_DIR="/backup/postgres"
   DATE=$(date +%Y%m%d_%H%M%S)
   
   # Create backup
   pg_dump -h postgres-host -U gateway -d gateway > "$BACKUP_DIR/gateway_$DATE.sql"
   
   # Compress backup
   gzip "$BACKUP_DIR/gateway_$DATE.sql"
   
   # Cleanup old backups (keep last 7 days)
   find "$BACKUP_DIR" -name "gateway_*.sql.gz" -mtime +7 -delete
   ```

2. **Redis backup:**
   ```bash
   #!/bin/bash
   BACKUP_DIR="/backup/redis"
   DATE=$(date +%Y%m%d_%H%M%S)
   
   # Create backup
   redis-cli --rdb "$BACKUP_DIR/dump_$DATE.rdb"
   
   # Cleanup old backups
   find "$BACKUP_DIR" -name "dump_*.rdb" -mtime +7 -delete
   ```

### Disaster Recovery

1. **Recovery procedures:**
   ```bash
   # Stop services
   docker-compose down
   
   # Restore database
   zcat /backup/postgres/gateway_latest.sql.gz | psql -h postgres-host -U gateway -d gateway
   
   # Restore Redis
   cp /backup/redis/dump_latest.rdb /var/lib/redis/dump.rdb
   
   # Start services
   docker-compose up -d
   ```

2. **Health check after recovery:**
   ```bash
   # Verify services
   curl http://localhost:8080/health
   redis-cli ping
   psql -h postgres-host -U gateway -d gateway -c "SELECT 1"
   
   # Check logs
   docker-compose logs gateway-manager
   ```

## Performance Tuning

### Database Optimization

```sql
-- PostgreSQL optimizations
-- postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200

-- Create indexes
CREATE INDEX CONCURRENTLY idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX CONCURRENTLY idx_requests_created_at ON requests(created_at);
CREATE INDEX CONCURRENTLY idx_tasks_status ON tasks(status);
```

### Redis Configuration

```bash
# redis.conf optimizations
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
tcp-keepalive 300
timeout 0
```

### Application Tuning

```python
# uvicorn with multiple workers
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --max-requests 1000 \
    --max-requests-jitter 100
```

## Troubleshooting

### Common Issues

1. **Service startup failures:**
   ```bash
   # Check logs
   docker-compose logs gateway-manager
   
   # Check configuration
   docker-compose config
   
   # Verify environment variables
   docker-compose exec gateway-manager env
   ```

2. **Database connection issues:**
   ```bash
   # Test database connectivity
   psql -h postgres-host -U gateway -d gateway -c "SELECT 1"
   
   # Check database logs
   docker-compose logs postgres
   
   # Verify network connectivity
   docker network ls
   docker network inspect <network_name>
   ```

3. **Performance issues:**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Check API response times
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/health
   
   # Monitor database performance
   psql -h postgres-host -U gateway -d gateway -c "
   SELECT query, calls, total_time, mean_time 
   FROM pg_stat_statements 
   ORDER BY total_time DESC LIMIT 10;"
   ```

### Performance Monitoring

```bash
# Monitor API performance
ab -n 1000 -c 10 -H "Authorization: Bearer test-key" \
   http://localhost:8080/api/v1/health

# Monitor database connections
psql -h postgres-host -U gateway -d gateway -c "
SELECT state, count(*) 
FROM pg_stat_activity 
WHERE datname='gateway' 
GROUP BY state;"

# Monitor Redis performance
redis-cli --latency-history -i 1
```
