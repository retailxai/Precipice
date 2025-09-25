"""
Endpoint schemas
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.models.endpoint_credential import EndpointType


class EndpointCredentialBase(BaseModel):
    """Base endpoint credential schema."""
    endpoint: EndpointType
    client_id: Optional[str] = None
    secret: Optional[str] = None
    tokens: Optional[Dict] = None
    expires_at: Optional[datetime] = None
    scopes: List[str] = []
    encrypted: bool = False


class EndpointCredentialCreate(EndpointCredentialBase):
    """Schema for creating endpoint credentials."""
    pass


class EndpointCredentialResponse(EndpointCredentialBase):
    """Schema for endpoint credential responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
