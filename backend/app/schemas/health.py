"""
Health check schemas
"""

from typing import Dict, Optional
from pydantic import BaseModel


class HealthSummary(BaseModel):
    """Health summary schema."""
    status: str
    database: str
    redis: str
    workers: str
    queue_depth: int
    rate_limits: Dict[str, str]


class HealthMetrics(BaseModel):
    """Detailed health metrics schema."""
    database_connections: int
    redis_memory_usage: str
    active_workers: int
    queue_depth: int
    error_rate: float
    response_time_p95: int
