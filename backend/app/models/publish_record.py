"""
Publish record model for tracking publication attempts
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PublishStatus(str, Enum):
    """Publish status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PublishRecord(Base):
    """Publish record model for tracking publication attempts."""
    
    __tablename__ = "publish_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    draft_id: Mapped[int] = mapped_column(Integer, ForeignKey("drafts.id"), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[PublishStatus] = mapped_column(SQLEnum(PublishStatus), default=PublishStatus.PENDING)
    request: Mapped[Optional[Dict]] = mapped_column(JSON, default=dict)
    response: Mapped[Optional[Dict]] = mapped_column(JSON, default=dict)
    external_url: Mapped[Optional[str]] = mapped_column(String(500))
    run_by: Mapped[Optional[str]] = mapped_column(String(100))
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    draft: Mapped["Draft"] = relationship("Draft", back_populates="publish_records")
    
    def __repr__(self) -> str:
        return f"<PublishRecord(id={self.id}, draft_id={self.draft_id}, endpoint='{self.endpoint}', status='{self.status}')>"
