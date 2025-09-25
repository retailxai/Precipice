"""
Endpoint credential model for publishing channels
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EndpointType(str, Enum):
    """Endpoint type enumeration."""
    SUBSTACK = "substack"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"


class EndpointCredential(Base):
    """Endpoint credential model for publishing channels."""
    
    __tablename__ = "endpoint_credentials"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    endpoint: Mapped[EndpointType] = mapped_column(SQLEnum(EndpointType), nullable=False)
    client_id: Mapped[Optional[str]] = mapped_column(String(255))
    secret: Mapped[Optional[str]] = mapped_column(String(500))
    tokens: Mapped[Optional[Dict]] = mapped_column(JSON, default=dict)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scopes: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<EndpointCredential(id={self.id}, endpoint='{self.endpoint}')>"
