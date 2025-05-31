# Gateway Manager API Reference

## Base URL
```
https://api.bitinglip.com/v1
```

## Authentication

All API requests require authentication using an API key in the Authorization header:

```http
Authorization: Bearer YOUR_API_KEY
```

### Getting an API Key

Contact your system administrator or use the user management interface to obtain an API key.

## Rate Limits

Rate limits vary by subscription tier:

| Tier | Requests/min | Requests/hour | Concurrent |
|------|--------------|---------------|------------|
| Free | 10 | 100 | 2 |
| Pro | 100 | 1,000 | 10 |
| Enterprise | 1,000 | 10,000 | 50 |

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    },
    "request_id": "req-12345-abcde",
    "timestamp": "2025-05-30T10:00:00Z"
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable - System overloaded |

## Inference API

### Text Generation

Generate text using large language models.

#### Endpoint
```http
POST /inference/text-generation
```

#### Request Body
```json
{
  "model": "llama-2-7b",
  "prompt": "Explain quantum computing in simple terms",
  "max_tokens": 512,
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 50,
  "stop_sequences": ["\n\n", "Human:", "AI:"],
  "stream": false
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model identifier |
| `prompt` | string | Yes | Input text prompt |
| `max_tokens` | integer | No | Maximum tokens to generate (default: 512) |
| `temperature` | float | No | Sampling temperature 0.0-2.0 (default: 0.7) |
| `top_p` | float | No | Nucleus sampling parameter (default: 0.9) |
| `top_k` | integer | No | Top-k sampling parameter (default: 50) |
| `stop_sequences` | array | No | Sequences to stop generation |
| `stream` | boolean | No | Enable streaming response (default: false) |

#### Response
```json
{
  "task_id": "task-12345-abcde",
  "status": "completed",
  "result": {
    "generated_text": "Quantum computing is a revolutionary technology...",
    "tokens_generated": 324,
    "finish_reason": "length",
    "model_used": "llama-2-7b"
  },
  "processing_time": 2.5,
  "worker_id": "worker-001",
  "created_at": "2025-05-30T10:00:00Z",
  "completed_at": "2025-05-30T10:00:02Z"
}
```

#### Streaming Response

When `stream: true`, responses are sent as Server-Sent Events:

```http
Content-Type: text/event-stream

data: {"token": "Quantum", "partial_text": "Quantum"}

data: {"token": " computing", "partial_text": "Quantum computing"}

data: {"done": true, "final_text": "Quantum computing is..."}
```

### Image Generation

Generate images from text descriptions.

#### Endpoint
```http
POST /inference/image-generation
```

#### Request Body
```json
{
  "model": "stable-diffusion-xl",
  "prompt": "A beautiful sunset over snow-capped mountains",
  "negative_prompt": "blurry, low quality, distorted",
  "width": 1024,
  "height": 1024,
  "steps": 50,
  "guidance_scale": 7.5,
  "seed": 42,
  "num_images": 1
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Image model identifier |
| `prompt` | string | Yes | Text description of desired image |
| `negative_prompt` | string | No | What to avoid in the image |
| `width` | integer | No | Image width in pixels (default: 1024) |
| `height` | integer | No | Image height in pixels (default: 1024) |
| `steps` | integer | No | Number of denoising steps (default: 50) |
| `guidance_scale` | float | No | How closely to follow prompt (default: 7.5) |
| `seed` | integer | No | Random seed for reproducibility |
| `num_images` | integer | No | Number of images to generate (default: 1) |

#### Response
```json
{
  "task_id": "task-67890-fghij",
  "status": "completed",
  "result": {
    "images": [
      {
        "url": "https://cdn.bitinglip.com/images/img-12345.png",
        "width": 1024,
        "height": 1024,
        "format": "png",
        "seed": 42
      }
    ],
    "model_used": "stable-diffusion-xl",
    "steps_completed": 50
  },
  "processing_time": 8.2,
  "worker_id": "worker-002",
  "created_at": "2025-05-30T10:01:00Z",
  "completed_at": "2025-05-30T10:01:08Z"
}
```

### Text-to-Speech

Convert text to speech audio.

#### Endpoint
```http
POST /inference/text-to-speech
```

#### Request Body
```json
{
  "model": "bark",
  "text": "Hello, welcome to BitingLip AI services!",
  "voice": "speaker_1",
  "language": "en",
  "speed": 1.0,
  "pitch": 1.0
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | TTS model identifier |
| `text` | string | Yes | Text to convert to speech |
| `voice` | string | No | Voice identifier (default: "speaker_0") |
| `language` | string | No | Language code (default: "en") |
| `speed` | float | No | Speech speed multiplier (default: 1.0) |
| `pitch` | float | No | Pitch adjustment (default: 1.0) |

#### Response
```json
{
  "task_id": "task-11111-aaaaa",
  "status": "completed",
  "result": {
    "audio_url": "https://cdn.bitinglip.com/audio/audio-12345.wav",
    "duration": 3.5,
    "format": "wav",
    "sample_rate": 22050,
    "model_used": "bark"
  },
  "processing_time": 1.8,
  "worker_id": "worker-003",
  "created_at": "2025-05-30T10:02:00Z",
  "completed_at": "2025-05-30T10:02:02Z"
}
```

## Model Management API

### List Models

Get information about available models.

#### Endpoint
```http
GET /models
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by model type: `text`, `image`, `audio` |
| `status` | string | Filter by status: `available`, `loading`, `error` |
| `limit` | integer | Number of results (default: 50, max: 100) |
| `offset` | integer | Pagination offset (default: 0) |

#### Response
```json
{
  "models": [
    {
      "id": "llama-2-7b",
      "name": "Llama 2 7B",
      "type": "text",
      "description": "Large language model for text generation",
      "status": "available",
      "size": "13.5 GB",
      "capabilities": ["text-generation", "conversation"],
      "supported_languages": ["en", "es", "fr", "de"],
      "max_context_length": 4096,
      "parameters": {
        "temperature": {"min": 0.0, "max": 2.0, "default": 0.7},
        "top_p": {"min": 0.0, "max": 1.0, "default": 0.9},
        "max_tokens": {"min": 1, "max": 4096, "default": 512}
      }
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

### Get Model Details

Get detailed information about a specific model.

#### Endpoint
```http
GET /models/{model_id}
```

#### Response
```json
{
  "id": "stable-diffusion-xl",
  "name": "Stable Diffusion XL",
  "type": "image",
  "description": "High-resolution text-to-image generation model",
  "status": "available",
  "version": "1.0",
  "size": "6.9 GB",
  "license": "CreativeML Open RAIL++-M",
  "capabilities": ["text-to-image", "image-to-image"],
  "supported_resolutions": [
    {"width": 1024, "height": 1024},
    {"width": 1152, "height": 896},
    {"width": 896, "height": 1152}
  ],
  "parameters": {
    "steps": {"min": 1, "max": 150, "default": 50},
    "guidance_scale": {"min": 1.0, "max": 20.0, "default": 7.5},
    "width": {"options": [512, 768, 1024], "default": 1024},
    "height": {"options": [512, 768, 1024], "default": 1024}
  },
  "performance_metrics": {
    "average_generation_time": 8.5,
    "gpu_memory_usage": "8.2 GB",
    "success_rate": 99.2
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-05-01T10:00:00Z"
}
```

### Download Model

Request download of a new model.

#### Endpoint
```http
POST /models/download
```

#### Request Body
```json
{
  "model_name": "llama-2-13b",
  "source": "huggingface",
  "priority": "normal",
  "auto_assign": true
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_name` | string | Yes | Model identifier or HuggingFace repo |
| `source` | string | No | Source platform (default: "huggingface") |
| `priority` | string | No | Download priority: "low", "normal", "high" |
| `auto_assign` | boolean | No | Auto-assign to workers when ready |

#### Response
```json
{
  "download_id": "dl-12345-abcde",
  "model_name": "llama-2-13b",
  "status": "downloading",
  "progress": 0,
  "estimated_size": "25.6 GB",
  "estimated_time": "15m",
  "created_at": "2025-05-30T10:03:00Z"
}
```

### Download Status

Check the status of a model download.

#### Endpoint
```http
GET /models/download/{download_id}/status
```

#### Response
```json
{
  "download_id": "dl-12345-abcde",
  "model_name": "llama-2-13b",
  "status": "downloading",
  "progress": 65,
  "downloaded_size": "16.6 GB",
  "total_size": "25.6 GB",
  "download_speed": "45.2 MB/s",
  "estimated_remaining": "4m 20s",
  "started_at": "2025-05-30T10:03:00Z",
  "updated_at": "2025-05-30T10:08:30Z"
}
```

## Cluster Management API

### Cluster Status

Get overall cluster health and status.

#### Endpoint
```http
GET /cluster/status
```

#### Response
```json
{
  "cluster_id": "biting-lip-main",
  "status": "operational",
  "uptime": "7d 4h 23m",
  "version": "1.2.3",
  "workers": {
    "total": 8,
    "online": 7,
    "offline": 1,
    "busy": 4
  },
  "tasks": {
    "queued": 12,
    "running": 8,
    "completed_today": 1247,
    "failed_today": 3
  },
  "resources": {
    "total_gpu_memory": "192 GB",
    "available_gpu_memory": "84 GB",
    "gpu_utilization": 67.5,
    "cpu_utilization": 45.2,
    "memory_utilization": 72.1
  },
  "performance": {
    "avg_response_time": "2.1s",
    "throughput": "120 tasks/hour",
    "success_rate": 99.7
  }
}
```

### List Workers

Get information about cluster workers.

#### Endpoint
```http
GET /workers
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `online`, `offline`, `busy`, `error` |
| `gpu_type` | string | Filter by GPU model |
| `limit` | integer | Number of results |
| `offset` | integer | Pagination offset |

#### Response
```json
{
  "workers": [
    {
      "id": "worker-001",
      "name": "GPU Node 1",
      "status": "online",
      "gpu_info": {
        "model": "AMD Radeon RX 7900 XTX",
        "memory_total": "24 GB",
        "memory_used": "8.2 GB",
        "utilization": 75.5,
        "temperature": 68
      },
      "system_info": {
        "cpu": "AMD Ryzen 9 7950X",
        "ram_total": "64 GB",
        "ram_used": "18.5 GB",
        "os": "Ubuntu 22.04"
      },
      "loaded_models": ["llama-2-7b", "stable-diffusion-xl"],
      "current_tasks": 2,
      "completed_tasks": 156,
      "uptime": "3d 2h 15m",
      "last_heartbeat": "2025-05-30T10:09:45Z"
    }
  ],
  "total": 8,
  "online": 7,
  "offline": 1
}
```

### Task Management

#### Get Task Status

Check the status of a specific task.

#### Endpoint
```http
GET /tasks/{task_id}
```

#### Response
```json
{
  "task_id": "task-12345-abcde",
  "status": "completed",
  "type": "text-generation",
  "model": "llama-2-7b",
  "assigned_worker": "worker-001",
  "priority": "normal",
  "progress": 100,
  "result": {
    "generated_text": "Quantum computing is a revolutionary technology..."
  },
  "processing_time": 2.5,
  "queue_time": 0.8,
  "total_time": 3.3,
  "created_at": "2025-05-30T10:00:00Z",
  "started_at": "2025-05-30T10:00:01Z",
  "completed_at": "2025-05-30T10:00:03Z"
}
```

#### Cancel Task

Cancel a queued or running task.

#### Endpoint
```http
DELETE /tasks/{task_id}
```

#### Response
```json
{
  "task_id": "task-12345-abcde",
  "status": "cancelled",
  "message": "Task cancelled successfully",
  "cancelled_at": "2025-05-30T10:00:15Z"
}
```

## WebSocket API

### Real-time Task Updates

Connect to receive real-time updates for inference tasks.

#### Endpoint
```
wss://api.bitinglip.com/v1/ws/tasks/{task_id}
```

#### Authentication
Include API key in connection header:
```javascript
const ws = new WebSocket('wss://api.bitinglip.com/v1/ws/tasks/task-12345', {
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY'
  }
});
```

#### Message Types

**Progress Update:**
```json
{
  "type": "progress",
  "task_id": "task-12345",
  "progress": 45,
  "status": "running",
  "estimated_remaining": "2.5s"
}
```

**Completion:**
```json
{
  "type": "completed",
  "task_id": "task-12345",
  "status": "completed",
  "result": {
    "generated_text": "Complete response..."
  },
  "processing_time": 2.5
}
```

**Error:**
```json
{
  "type": "error",
  "task_id": "task-12345",
  "status": "failed",
  "error": {
    "code": "MODEL_ERROR",
    "message": "Model failed to generate response"
  }
}
```

## Code Examples

### Python Client

```python
import requests
import json

class BitingLipClient:
    def __init__(self, api_key, base_url="https://api.bitinglip.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def generate_text(self, model, prompt, **kwargs):
        data = {
            "model": model,
            "prompt": prompt,
            **kwargs
        }
        response = self.session.post(
            f"{self.base_url}/inference/text-generation",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def generate_image(self, model, prompt, **kwargs):
        data = {
            "model": model,
            "prompt": prompt,
            **kwargs
        }
        response = self.session.post(
            f"{self.base_url}/inference/image-generation",
            json=data
        )
        response.raise_for_status()
        return response.json()

# Usage
client = BitingLipClient("your-api-key")

# Generate text
result = client.generate_text(
    model="llama-2-7b",
    prompt="Explain machine learning",
    max_tokens=300,
    temperature=0.7
)

print(result["result"]["generated_text"])
```

### JavaScript Client

```javascript
class BitingLipClient {
    constructor(apiKey, baseUrl = 'https://api.bitinglip.com/v1') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    }

    async generateText(model, prompt, options = {}) {
        return this.request('/inference/text-generation', {
            method: 'POST',
            body: JSON.stringify({
                model,
                prompt,
                ...options
            })
        });
    }

    async generateImage(model, prompt, options = {}) {
        return this.request('/inference/image-generation', {
            method: 'POST',
            body: JSON.stringify({
                model,
                prompt,
                ...options
            })
        });
    }
}

// Usage
const client = new BitingLipClient('your-api-key');

// Generate text
client.generateText('llama-2-7b', 'Explain quantum computing')
    .then(result => console.log(result.result.generated_text))
    .catch(error => console.error('Error:', error));
```

### cURL Examples

**Text Generation:**
```bash
curl -X POST "https://api.bitinglip.com/v1/inference/text-generation" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "llama-2-7b",
       "prompt": "Explain quantum computing",
       "max_tokens": 512,
       "temperature": 0.7
     }'
```

**Image Generation:**
```bash
curl -X POST "https://api.bitinglip.com/v1/inference/image-generation" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "stable-diffusion-xl",
       "prompt": "A beautiful sunset over mountains",
       "width": 1024,
       "height": 1024
     }'
```

**Check Task Status:**
```bash
curl -X GET "https://api.bitinglip.com/v1/tasks/task-12345-abcde" \
     -H "Authorization: Bearer YOUR_API_KEY"
```
