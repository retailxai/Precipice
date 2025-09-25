"""
Job model for async task management
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type enumeration."""
    PUBLISH = "publish"
    ANALYZE = "analyze"
    AI_IMPROVE = "ai_improve"
    AI_SHORTEN = "ai_shorten"
    AI_EXPAND = "ai_expand"
    AI_TITLES = "ai_titles"
    AI_SUMMARY = "ai_summary"


class Job(Base):
    """Job model for async task management."""
    
    __tablename__ = "jobs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[JobType] = mapped_column(SQLEnum(JobType), nullable=False)
    payload: Mapped[Dict] = mapped_column(JSON, default=dict)
    status: Mapped[JobStatus] = mapped_column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    queued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_text: Mapped[Optional[str]] = mapped_column(String(1000))
    
    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type='{self.type}', status='{self.status}')>"
