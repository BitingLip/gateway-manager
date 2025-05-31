# Gateway Manager 🚀 ⚙️

**Status**: Operational | **Type**: API Gateway Service | **Tech**: FastAPI, Redis

Primary API interface for the BitingLip AI inference cluster, providing unified access to all AI services.

## Core Features

- **Multi-Modal API**: Text generation, image generation, text-to-speech
- **Authentication & Authorization**: API key management with role-based access
- **Rate Limiting**: Tier-based throttling and quota management
- **Request Routing**: Intelligent load balancing to backend services
- **Real-time Updates**: WebSocket support for streaming responses
- **OpenAPI Documentation**: Auto-generated Swagger/OpenAPI specs

## Quick Start

```bash
# Start the API gateway
cd gateway-manager
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Start Redis (required)
redis-server

# Run development server
python start_server.py
# API available at http://localhost:8080

# Test the API
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8080/api/v1/health
```

## Documentation

| Topic | Description | Link |
|-------|-------------|------|
| **Architecture** | System design and components | [docs/architecture.md](docs/architecture.md) |
| **API Reference** | Complete API documentation | [docs/api.md](docs/api.md) |
| **Development** | Setup and development guide | [docs/development.md](docs/development.md) |
| **Deployment** | Production deployment guide | [docs/deployment.md](docs/deployment.md) |

## Integration

**Upstream Dependencies:**
- `cluster-manager`: Task distribution and worker management
- `model-manager`: Model information and lifecycle
- `task-manager`: Task status and result storage

**Configuration:**
- `CLUSTER_MANAGER_URL`: Cluster management service endpoint
- `MODEL_MANAGER_URL`: Model management service endpoint  
- `REDIS_URL`: Cache and session storage
- `API_KEY_SECRET`: JWT signing key
                           │                          │
                           │ (Interaction for         ▼
                           │  model info, etc.)   ┌────────────────┐
                           ▼                          │ Message Broker │
                    ┌──────────────────┐    │   (Redis)      │
                    │  Model Manager   │◀─────────┘
                    └──────────────────┘
```

The Gateway Manager receives requests, validates them, and then typically dispatches tasks to the `cluster-manager` (via a message broker like Redis with Celery). For model-specific information or operations like initiating a model download, it will communicate with the `model-manager`.

## Quick Start

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Environment
```powershell
copy .env.example .env
# Edit .env with your configuration
```

### 3. Start the API Server
```powershell
# Ensure Redis (or other dependencies like model-manager if it runs as a service) is running
start_api.bat 
# or: python start_server.py
```

### 4. Access Documentation
- API Documentation: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## Configuration

Environment variables in `.env`:
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8080)
- `REDIS_URL`: Redis broker connection string (for Celery task dispatching).
- `MODEL_MANAGER_URL` (New/Example): URL for the `model-manager` API if it runs as a separate service and the gateway needs to communicate with it directly.
- `API_KEYS`: Comma-separated list of valid API keys
- `RATE_LIMIT`: Requests per minute per API key
- `DEBUG`: Enable debug mode (default: False)

## Request/Response Format

### Text Generation Example
```bash
curl -X POST "http://localhost:8080/api/v1/inference/text-generation" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "gpt2",
    "prompt": "The future of AI is",
    "max_length": 100,
    "temperature": 0.7
  }'
```

### Response Format
```json
{
  "task_id": "uuid-string",
  "status": "pending|processing|completed|failed",
  "result": "Generated text...",
  "metadata": {
    "processing_time": 5.2,
    "worker_id": "worker-01",
    "model_info": {...}
  }
}
```

## Error Handling

The API returns standard HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid API key)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error
- `503`: Service Unavailable (cluster unavailable)

## Dependencies

See `requirements.txt` for full dependencies. Key packages:
- `fastapi`: Modern web framework
- `uvicorn`: ASGI server
- `celery[redis]`: Task queue integration
- `pydantic`: Data validation
- `redis`: Redis client