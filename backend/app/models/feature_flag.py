"""
Feature flag model for configuration management
"""

from datetime import datetime
from typing import Dict, Optional
from sqlalchemy import Column, String, DateTime, JSON, Boolean, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FeatureFlag(Base):
    """Feature flag model for configuration management."""
    
    __tablename__ = "feature_flags"
    __table_args__ = (PrimaryKeyConstraint("key"),)
    
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[Optional[Dict]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<FeatureFlag(key='{self.key}', enabled={self.enabled})>"
