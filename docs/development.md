# Gateway Manager Development Guide

## Development Environment Setup

### Prerequisites
- Python 3.10+
- Redis server
- Git
- Node.js (for API testing tools)

### Initial Setup

1. **Clone and enter the module:**
   ```bash
   cd gateway-manager
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate   # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start Redis server:**
   ```bash
   redis-server
   ```

6. **Run the development server:**
   ```bash
   python start_server.py
   # or
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

### Environment Configuration

Key environment variables in `.env`:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
API_VERSION=v1
DEBUG=true

# Security
SECRET_KEY=your-secret-key-for-development
API_KEY_EXPIRY=86400
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Service URLs
CLUSTER_MANAGER_URL=http://localhost:8000
MODEL_MANAGER_URL=http://localhost:8001
TASK_MANAGER_URL=http://localhost:8002

# Database
DATABASE_URL=postgresql://user:pass@localhost/gateway
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT=100/hour

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text
```

## Project Structure

```
gateway-manager/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── models/              # Pydantic models and schemas
│   │   ├── __init__.py
│   │   ├── requests.py      # Request models
│   │   ├── responses.py     # Response models
│   │   └── auth.py          # Authentication models
│   ├── api/                 # API route handlers
│   │   ├── __init__.py
│   │   ├── v1/              # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── inference.py     # Inference endpoints
│   │   │   ├── models.py        # Model management endpoints
│   │   │   ├── cluster.py       # Cluster endpoints
│   │   │   └── auth.py          # Authentication endpoints
│   │   └── dependencies.py  # Shared dependencies
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Authentication logic
│   │   ├── inference_service.py # Inference coordination
│   │   ├── model_service.py     # Model management
│   │   └── cluster_service.py   # Cluster communication
│   ├── middleware/          # Custom middleware
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication middleware
│   │   ├── rate_limiter.py  # Rate limiting middleware
│   │   ├── cors.py          # CORS middleware
│   │   └── logging.py       # Request logging
│   ├── core/                # Core configurations
│   │   ├── __init__.py
│   │   ├── config.py        # Application configuration
│   │   ├── security.py      # Security utilities
│   │   └── exceptions.py    # Custom exceptions
│   └── utils/               # Utility modules
│       ├── __init__.py
│       ├── http_client.py   # HTTP client utilities
│       ├── cache.py         # Caching utilities
│       └── validators.py    # Custom validators
├── tests/                   # Test files
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── conftest.py         # Pytest configuration
├── docs/                   # Detailed documentation
├── scripts/                # Utility scripts
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies
├── .env.example           # Environment template
├── start_server.py        # Development server script
└── README.md              # Minimal overview
```

## Development Workflow

### 1. Feature Development

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement changes:**
   - Add/modify API endpoints in `app/api/v1/`
   - Implement business logic in `app/services/`
   - Add data models in `app/models/`
   - Follow coding standards (see below)

3. **Test your changes:**
   ```bash
   # Run unit tests
   pytest tests/unit/ -v
   
   # Run integration tests
   pytest tests/integration/ -v
   
   # Run all tests with coverage
   pytest --cov=app --cov-report=html
   
   # Test specific endpoint
   pytest tests/unit/test_inference_api.py::test_text_generation -v
   ```

4. **Test API manually:**
   ```bash
   # Start development server
   python start_server.py
   
   # Test endpoints
   curl -X GET http://localhost:8080/health
   curl -X GET http://localhost:8080/docs  # Swagger UI
   ```

### 2. API Development

#### Adding New Endpoints

1. **Define request/response models:**
   ```python
   # app/models/requests.py
   class NewFeatureRequest(BaseModel):
       parameter: str
       options: Optional[Dict[str, Any]] = None
   
   # app/models/responses.py
   class NewFeatureResponse(BaseModel):
       result: str
       processing_time: float
   ```

2. **Implement service logic:**
   ```python
   # app/services/new_feature_service.py
   class NewFeatureService:
       def __init__(self, http_client: HTTPClient):
           self.http_client = http_client
       
       async def process_request(self, request: NewFeatureRequest) -> NewFeatureResponse:
           # Implement business logic
           pass
   ```

3. **Create API endpoint:**
   ```python
   # app/api/v1/new_feature.py
   from fastapi import APIRouter, Depends
   from app.models.requests import NewFeatureRequest
   from app.models.responses import NewFeatureResponse
   from app.services.new_feature_service import NewFeatureService
   
   router = APIRouter()
   
   @router.post("/new-feature", response_model=NewFeatureResponse)
   async def new_feature_endpoint(
       request: NewFeatureRequest,
       service: NewFeatureService = Depends(get_new_feature_service)
   ):
       return await service.process_request(request)
   ```

4. **Register router:**
   ```python
   # app/main.py
   from app.api.v1.new_feature import router as new_feature_router
   
   app.include_router(
       new_feature_router,
       prefix="/api/v1",
       tags=["new-feature"]
   )
   ```

### 3. Testing

#### Unit Tests
```bash
# Run specific test file
pytest tests/unit/test_auth_service.py -v

# Run tests with specific marker
pytest -m "not integration" -v

# Run tests with coverage
pytest tests/unit/ --cov=app.services --cov-report=term-missing
```

#### Integration Tests
```bash
# Start test dependencies
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/ -v

# Cleanup
docker-compose -f docker-compose.test.yml down
```

#### API Tests
```bash
# Install testing tools
pip install httpx pytest-asyncio

# Example test
# tests/integration/test_inference_api.py
import pytest
import httpx
from app.main import app

@pytest.mark.asyncio
async def test_text_generation():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/inference/text-generation",
            json={
                "model": "test-model",
                "prompt": "Hello world",
                "max_tokens": 50
            },
            headers={"Authorization": "Bearer test-api-key"}
        )
        assert response.status_code == 200
        assert "result" in response.json()
```

### 4. Debugging

#### FastAPI Debug Mode
```python
# app/main.py
from fastapi import FastAPI
import logging

# Enable debug mode
app = FastAPI(debug=True)

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request, call_next):
    logger.debug(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Response: {response.status_code}")
    return response
```

#### Database Debugging
```python
# Enable SQLAlchemy logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### Redis Debugging
```bash
# Monitor Redis commands
redis-cli monitor

# Check Redis keys
redis-cli keys "*"

# Get Redis info
redis-cli info
```

## Coding Standards

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Maximum line length: 88 characters
- Use black for code formatting

```bash
# Format code
black app/ tests/

# Check code style
flake8 app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/
```

### API Design Standards

#### Request/Response Models
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class APIRequest(BaseModel):
    """Base request model with common fields."""
    request_id: Optional[str] = Field(None, description="Optional request ID")
    
class APIResponse(BaseModel):
    """Base response model with common fields."""
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time: Optional[float] = None

class TextGenerationRequest(APIRequest):
    model: str = Field(..., description="Model identifier")
    prompt: str = Field(..., min_length=1, description="Input prompt")
    max_tokens: int = Field(512, ge=1, le=4096, description="Maximum tokens")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
```

#### Error Handling
```python
from fastapi import HTTPException
from app.core.exceptions import APIError

class InferenceError(APIError):
    """Raised when inference fails."""
    pass

@router.post("/inference/text-generation")
async def generate_text(request: TextGenerationRequest):
    try:
        result = await inference_service.generate_text(request)
        return result
    except InferenceError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

#### Documentation
```python
@router.post(
    "/inference/text-generation",
    response_model=TextGenerationResponse,
    summary="Generate text using LLM",
    description="Generate text using a large language model with specified parameters.",
    responses={
        200: {"description": "Text generated successfully"},
        400: {"description": "Invalid request parameters"},
        401: {"description": "Invalid API key"},
        422: {"description": "Model error or processing failure"},
        429: {"description": "Rate limit exceeded"}
    }
)
async def generate_text(request: TextGenerationRequest):
    """Generate text using a large language model.
    
    Args:
        request: Text generation parameters
        
    Returns:
        Generated text response with metadata
        
    Raises:
        HTTPException: For various error conditions
    """
    pass
```

## Performance Optimization

### Async Programming
```python
import asyncio
import httpx
from typing import List

# Use async HTTP clients
async def call_multiple_services(requests: List[dict]) -> List[dict]:
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post(f"{service_url}/endpoint", json=req)
            for req in requests
        ]
        responses = await asyncio.gather(*tasks)
        return [resp.json() for resp in responses]

# Use async database operations
from databases import Database

async def get_user_data(user_id: str) -> dict:
    query = "SELECT * FROM users WHERE id = :user_id"
    return await database.fetch_one(query, values={"user_id": user_id})
```

### Caching
```python
import redis.asyncio as redis
from functools import wraps

# Redis caching decorator
def cache_result(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(ttl=600)
async def get_model_info(model_id: str) -> dict:
    # Expensive operation
    pass
```

### Connection Pooling
```python
# HTTP client with connection pooling
import httpx

class HTTPClientManager:
    def __init__(self):
        self.limits = httpx.Limits(
            max_keepalive_connections=100,
            max_connections=200,
            keepalive_expiry=30
        )
        self.client = httpx.AsyncClient(limits=self.limits)
    
    async def close(self):
        await self.client.aclose()

# Database connection pooling
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600
)
```

## Security Best Practices

### Input Validation
```python
from pydantic import validator
import re

class TextGenerationRequest(BaseModel):
    prompt: str
    
    @validator('prompt')
    def validate_prompt(cls, v):
        # Remove potential injection attempts
        if re.search(r'<script|javascript:|data:', v, re.IGNORECASE):
            raise ValueError('Invalid prompt content')
        
        # Limit prompt length
        if len(v) > 10000:
            raise ValueError('Prompt too long')
        
        return v.strip()
```

### API Key Security
```python
from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return pwd_context.hash(api_key)

def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify API key against hash."""
    return pwd_context.verify(plain_key, hashed_key)
```

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/inference/text-generation")
@limiter.limit("10/minute")
async def generate_text(request: Request, ...):
    pass
```

## Monitoring and Observability

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    'gateway_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'gateway_request_duration_seconds',
    'Request duration'
)

# Business metrics
INFERENCE_COUNT = Counter(
    'inference_requests_total',
    'Total inference requests',
    ['model_type', 'model_name']
)

ACTIVE_CONNECTIONS = Gauge(
    'gateway_active_connections',
    'Number of active connections'
)
```

### Structured Logging
```python
import structlog

logger = structlog.get_logger(__name__)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    logger.info(
        "request_started",
        method=request.method,
        url=str(request.url),
        user_agent=request.headers.get("user-agent")
    )
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(
        "request_completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        duration=duration
    )
    
    return response
```

## Troubleshooting

### Common Issues

1. **Service Connection Errors:**
   ```bash
   # Check service connectivity
   curl http://cluster-manager:8000/health
   curl http://model-manager:8001/health
   
   # Check DNS resolution
   nslookup cluster-manager
   ping cluster-manager
   ```

2. **Redis Connection Issues:**
   ```bash
   # Test Redis connection
   redis-cli -h redis-host ping
   
   # Check Redis logs
   tail -f /var/log/redis/redis-server.log
   ```

3. **Authentication Problems:**
   ```bash
   # Test API key
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        http://localhost:8080/api/v1/health
   
   # Check logs for auth errors
   grep "authentication" logs/gateway.log
   ```

### Debug Commands
```bash
# Check API health
curl http://localhost:8080/health

# View OpenAPI docs
open http://localhost:8080/docs

# Monitor requests
tail -f logs/gateway.log

# Check Redis status
redis-cli info

# Test database connection
python -c "
from app.core.database import engine
import asyncio
async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('DB OK')
asyncio.run(test())
"
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation as needed
7. Submit a pull request

### Pull Request Guidelines
- Include clear description of changes
- Reference related issues
- Include test coverage for new features
- Update API documentation if endpoints change
- Follow semantic versioning for breaking changes
