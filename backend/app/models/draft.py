"""
Draft model for content management
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DraftStatus(str, Enum):
    """Draft status enumeration."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Draft(Base):
    """Draft model for content management."""
    
    __tablename__ = "drafts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body_md: Mapped[Optional[str]] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    hero_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    source: Mapped[Optional[str]] = mapped_column(String(100))
    source_ref: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[DraftStatus] = mapped_column(SQLEnum(DraftStatus), default=DraftStatus.DRAFT)
    scores: Mapped[Optional[Dict]] = mapped_column(JSON, default=dict)
    meta: Mapped[Optional[Dict]] = mapped_column(JSON, default=dict)
    
    # Relationships
    publish_records: Mapped[List["PublishRecord"]] = relationship("PublishRecord", back_populates="draft")
    
    def __repr__(self) -> str:
        return f"<Draft(id={self.id}, title='{self.title}', status='{self.status}')>"
