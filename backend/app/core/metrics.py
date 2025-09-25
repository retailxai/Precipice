"""
Prometheus metrics for RetailXAI Dashboard
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Business metrics
DRAFTS_CREATED = Counter(
    'drafts_created_total',
    'Total drafts created'
)

DRAFTS_PUBLISHED = Counter(
    'drafts_published_total',
    'Total drafts published',
    ['endpoint']
)

PUBLISH_FAILURES = Counter(
    'publish_failures_total',
    'Total publish failures',
    ['endpoint', 'error_type']
)

# System metrics
ACTIVE_JOBS = Gauge(
    'active_jobs_total',
    'Number of active jobs',
    ['job_type']
)

QUEUE_DEPTH = Gauge(
    'queue_depth_total',
    'Number of items in queue',
    ['queue_name']
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

# Application info
APP_INFO = Info(
    'app_info',
    'Application information'
)

# Middleware for request metrics
class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        method = scope["method"]
        path = scope["path"]
        
        # Normalize path for metrics (remove IDs)
        endpoint = self._normalize_path(path)
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = str(message["status"])
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
        
        duration = time.time() - start_time
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing IDs with placeholders."""
        import re
        # Replace UUIDs and numbers with placeholders
        path = re.sub(r'/[0-9a-f-]{8,}', '/{id}', path)
        path = re.sub(r'/\d+', '/{id}', path)
        return path
