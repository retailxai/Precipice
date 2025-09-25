"""
Job schemas
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.models.job import JobStatus, JobType


class JobResponse(BaseModel):
    """Job response schema."""
    id: int
    type: JobType
    payload: Dict
    status: JobStatus
    queued_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    attempts: int
    error_text: Optional[str]
    
    class Config:
        from_attributes = True


class JobList(BaseModel):
    """Job list schema."""
    jobs: List[JobResponse]
    total: int
