"""
Prometheus metrics configuration
"""

from prometheus_client import Counter, Histogram, Gauge


# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration')
ACTIVE_TASKS = Gauge('active_tasks_total', 'Number of active tasks')
PENDING_TASKS = Gauge('pending_tasks_total', 'Number of pending tasks')
COMPLETED_TASKS = Counter('completed_tasks_total', 'Total completed tasks', ['status'])
