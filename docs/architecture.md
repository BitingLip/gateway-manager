# Gateway Manager Architecture

## Overview

The Gateway Manager serves as the primary API gateway for the BitingLip AI inference cluster, providing a unified interface for client applications to access various AI services including text generation, image generation, and model management.

## System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Web[Web Applications]
        Mobile[Mobile Apps]
        CLI[CLI Tools]
        API[API Clients]
    end
    
    subgraph "Gateway Manager"
        Router[FastAPI Router]
        Auth[Authentication]
        Validation[Input Validation]
        RateLimit[Rate Limiting]
        LoadBalancer[Load Balancer]
    end
    
    subgraph "Backend Services"
        CM[Cluster Manager]
        MM[Model Manager]
        TM[Task Manager]
    end
    
    subgraph "Infrastructure"
        Redis[(Redis Cache)]
        DB[(PostgreSQL)]
        Metrics[Prometheus]
    end
    
    Web --> Router
    Mobile --> Router
    CLI --> Router
    API --> Router
    
    Router --> Auth
    Auth --> Validation
    Validation --> RateLimit
    RateLimit --> LoadBalancer
    
    LoadBalancer --> CM
    LoadBalancer --> MM
    LoadBalancer --> TM
    
    Auth --> Redis
    RateLimit --> Redis
    Router --> DB
    Router --> Metrics
```

## Core Components

### 1. API Router (`app/main.py`)
- **Purpose**: Central FastAPI application with route definitions
- **Features**:
  - OpenAPI/Swagger documentation
  - CORS handling
  - Error handling middleware
  - Health checks and monitoring

### 2. Authentication Service (`app/services/auth.py`)
- **Purpose**: Handles API key validation and user authentication
- **Features**:
  - API key management
  - JWT token validation
  - User session management
  - Permission-based access control

### 3. Request Validation (`app/validators/`)
- **Purpose**: Validates incoming requests against schemas
- **Components**:
  - Pydantic models for request/response validation
  - Custom validators for AI-specific parameters
  - Sanitization and normalization

### 4. Rate Limiting (`app/middleware/rate_limiter.py`)
- **Purpose**: Implements request throttling and quota management
- **Features**:
  - Per-user rate limiting
  - Endpoint-specific limits
  - Burst handling
  - Quota tracking

### 5. Load Balancer (`app/services/load_balancer.py`)
- **Purpose**: Routes requests to appropriate backend services
- **Algorithms**:
  - Round-robin distribution
  - Weighted routing based on service health
  - Sticky sessions for stateful operations

## API Endpoints

### Inference Endpoints

#### Text Generation
```http
POST /api/v1/inference/text-generation
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "model": "llama-2-7b",
  "prompt": "Explain quantum computing",
  "max_tokens": 512,
  "temperature": 0.7,
  "top_p": 0.9
}
```

#### Image Generation
```http
POST /api/v1/inference/image-generation
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "model": "stable-diffusion-xl",
  "prompt": "A beautiful sunset over mountains",
  "width": 1024,
  "height": 1024,
  "steps": 50,
  "guidance_scale": 7.5
}
```

#### Text-to-Speech
```http
POST /api/v1/inference/text-to-speech
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "model": "bark",
  "text": "Hello, how are you today?",
  "voice": "speaker_1",
  "language": "en"
}
```

### Model Management Endpoints

#### List Models
```http
GET /api/v1/models
Authorization: Bearer <api_key>

Query Parameters:
- type: filter by model type (text, image, audio)
- status: filter by status (available, loading, error)
- limit: number of results (default: 50)
- offset: pagination offset
```

#### Model Details
```http
GET /api/v1/models/{model_id}
Authorization: Bearer <api_key>
```

#### Download Model
```http
POST /api/v1/models/download
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "model_name": "llama-2-13b",
  "source": "huggingface",
  "priority": "normal"
}
```

### Cluster Management Endpoints

#### Cluster Status
```http
GET /api/v1/cluster/status
Authorization: Bearer <api_key>
```

#### Worker Management
```http
GET /api/v1/workers
POST /api/v1/workers/{worker_id}/restart
DELETE /api/v1/workers/{worker_id}
```

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant GW as Gateway
    participant Auth as Auth Service
    participant RL as Rate Limiter
    participant CM as Cluster Manager
    participant W as Worker
    
    C->>GW: POST /api/v1/inference/text-generation
    GW->>Auth: Validate API key
    Auth->>GW: Authentication result
    GW->>RL: Check rate limits
    RL->>GW: Rate limit status
    GW->>GW: Validate request payload
    GW->>CM: Forward inference request
    CM->>W: Assign task to worker
    W->>CM: Return results
    CM->>GW: Forward results
    GW->>C: Return response
```

## Data Models

### Request Models
```python
class TextGenerationRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    stream: bool = False

class ImageGenerationRequest(BaseModel):
    model: str
    prompt: str
    width: int = 1024
    height: int = 1024
    steps: int = 50
    guidance_scale: float = 7.5
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
```

### Response Models
```python
class InferenceResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    worker_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ModelInfo(BaseModel):
    model_id: str
    name: str
    type: ModelType
    description: str
    size: str
    status: ModelStatus
    capabilities: List[str]
    supported_parameters: Dict[str, Any]
```

## Authentication & Authorization

### API Key Management
- **Generation**: Unique API keys per user/application
- **Validation**: JWT-based token validation
- **Scopes**: Different permission levels (read, write, admin)
- **Rotation**: Automatic key rotation and revocation

### Access Control
```python
class APIKeyScopes:
    READ_MODELS = "models:read"
    INFERENCE_TEXT = "inference:text"
    INFERENCE_IMAGE = "inference:image"
    INFERENCE_AUDIO = "inference:audio"
    CLUSTER_READ = "cluster:read"
    CLUSTER_WRITE = "cluster:write"
    ADMIN = "admin"
```

## Rate Limiting Strategy

### Tier-Based Limits
```python
RATE_LIMITS = {
    "free": {
        "requests_per_minute": 10,
        "requests_per_hour": 100,
        "concurrent_requests": 2
    },
    "pro": {
        "requests_per_minute": 100,
        "requests_per_hour": 1000,
        "concurrent_requests": 10
    },
    "enterprise": {
        "requests_per_minute": 1000,
        "requests_per_hour": 10000,
        "concurrent_requests": 50
    }
}
```

### Adaptive Rate Limiting
- Dynamic adjustment based on system load
- Priority queues for different user tiers
- Burst allowances for occasional spikes
- Graceful degradation under high load

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_MODEL",
    "message": "The specified model is not available",
    "details": {
      "model": "invalid-model-name",
      "available_models": ["llama-2-7b", "stable-diffusion-xl"]
    },
    "request_id": "req-12345",
    "timestamp": "2025-05-30T10:00:00Z"
  }
}
```

### Error Categories
- **4xx Client Errors**: Invalid requests, authentication failures
- **5xx Server Errors**: Internal errors, service unavailable
- **Custom Errors**: AI-specific errors (model loading, inference failures)

## Caching Strategy

### Response Caching
- **TTL-based caching** for model information
- **Content-based caching** for repeated inference requests
- **User-specific caching** with permission awareness

### Cache Implementation
```python
@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    cache_key = generate_cache_key(request)
    
    # Check cache
    cached_response = await redis_client.get(cache_key)
    if cached_response and is_cacheable(request):
        return JSONResponse(json.loads(cached_response))
    
    # Process request
    response = await call_next(request)
    
    # Store in cache
    if should_cache(response):
        await redis_client.setex(
            cache_key, 
            CACHE_TTL, 
            response.body.decode()
        )
    
    return response
```

## Performance Optimization

### Connection Pooling
- **HTTP Connection Pools** for backend services
- **Database Connection Pooling** with pgbouncer
- **Redis Connection Pooling** for caching

### Async Processing
- **Background Tasks** for non-blocking operations
- **Stream Processing** for large responses
- **Batch Processing** for multiple requests

### Resource Management
```python
# Connection pool configuration
HTTPX_LIMITS = httpx.Limits(
    max_keepalive_connections=100,
    max_connections=200,
    keepalive_expiry=30
)

# Database pool settings
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_TIMEOUT = 30
```

## Monitoring & Observability

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    'gateway_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'gateway_request_duration_seconds',
    'Request duration'
)

# Business metrics
INFERENCE_COUNT = Counter(
    'inference_requests_total',
    'Total inference requests',
    ['model', 'type']
)

ACTIVE_USERS = Gauge(
    'gateway_active_users',
    'Number of active users'
)
```

### Distributed Tracing
- **OpenTelemetry** integration for request tracing
- **Correlation IDs** for request tracking across services
- **Performance profiling** for bottleneck identification

### Health Checks
```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "cluster_manager": await check_cluster_manager(),
        "model_manager": await check_model_manager()
    }
    
    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow(),
        "version": __version__
    }
```

## Security Considerations

### Input Sanitization
- **SQL Injection Protection** via parameterized queries
- **XSS Prevention** with proper encoding
- **Command Injection Prevention** for AI prompts

### Network Security
- **TLS Encryption** for all communications
- **CORS Configuration** for web client access
- **IP Whitelisting** for enterprise clients

### Data Protection
- **PII Detection** in prompts and responses
- **Content Filtering** for inappropriate content
- **Audit Logging** for compliance requirements

## Integration Points

### Upstream Services
```python
class ServiceClients:
    def __init__(self):
        self.cluster_manager = httpx.AsyncClient(
            base_url="http://cluster-manager:8000"
        )
        self.model_manager = httpx.AsyncClient(
            base_url="http://model-manager:8001"
        )
        self.task_manager = httpx.AsyncClient(
            base_url="http://task-manager:8002"
        )
```

### WebSocket Support
```python
@app.websocket("/ws/inference/{task_id}")
async def websocket_inference(websocket: WebSocket, task_id: str):
    await websocket.accept()
    
    # Stream real-time updates
    async for update in stream_task_updates(task_id):
        await websocket.send_json(update)
```

## Configuration Management

### Environment-based Configuration
```python
class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_version: str = "v1"
    
    # Service URLs
    cluster_manager_url: str = "http://cluster-manager:8000"
    model_manager_url: str = "http://model-manager:8001"
    task_manager_url: str = "http://task-manager:8002"
    
    # Database
    database_url: str = "postgresql://user:pass@localhost/gateway"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    api_key_expiry: int = 86400  # 24 hours
    
    class Config:
        env_file = ".env"
```
