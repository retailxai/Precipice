"""
Draft schemas for API requests and responses
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.draft import DraftStatus


class DraftBase(BaseModel):
    """Base draft schema."""
    title: str = Field(..., max_length=500)
    body_md: Optional[str] = None
    body_html: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    hero_image_url: Optional[str] = Field(None, max_length=500)
    source: Optional[str] = Field(None, max_length=100)
    source_ref: Optional[str] = Field(None, max_length=255)
    author: Optional[str] = Field(None, max_length=100)
    status: DraftStatus = DraftStatus.DRAFT
    scores: Optional[Dict] = Field(default_factory=dict)
    meta: Optional[Dict] = Field(default_factory=dict)


class DraftCreate(DraftBase):
    """Schema for creating a draft."""
    slug: str = Field(..., max_length=255)


class DraftUpdate(BaseModel):
    """Schema for updating a draft."""
    title: Optional[str] = Field(None, max_length=500)
    body_md: Optional[str] = None
    body_html: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    hero_image_url: Optional[str] = Field(None, max_length=500)
    source: Optional[str] = Field(None, max_length=100)
    source_ref: Optional[str] = Field(None, max_length=255)
    author: Optional[str] = Field(None, max_length=100)
    status: Optional[DraftStatus] = None
    scores: Optional[Dict] = None
    meta: Optional[Dict] = None


class DraftResponse(DraftBase):
    """Schema for draft responses."""
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DraftList(BaseModel):
    """Schema for draft list responses."""
    drafts: List[DraftResponse]
    total: int
    page: int
    size: int
    pages: int


class DraftAnalyzeRequest(BaseModel):
    """Schema for draft analysis requests."""
    analysis_type: str = Field(..., description="Type of analysis to perform")
    parameters: Optional[Dict] = Field(default_factory=dict)


class DraftAIRequest(BaseModel):
    """Schema for AI improvement requests."""
    action: str = Field(..., description="AI action: improve, shorten, expand, titles, summary")
    parameters: Optional[Dict] = Field(default_factory=dict)


class DraftPreviewRequest(BaseModel):
    """Schema for draft preview requests."""
    endpoint: str = Field(..., description="Endpoint to preview for")
    parameters: Optional[Dict] = Field(default_factory=dict)


class DraftPublishRequest(BaseModel):
    """Schema for draft publishing requests."""
    endpoints: List[str] = Field(..., description="List of endpoints to publish to")
    parameters: Optional[Dict] = Field(default_factory=dict)
