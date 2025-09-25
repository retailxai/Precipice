"""
Audit log schemas
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """Audit log response schema."""
    id: int
    actor: str
    action: str
    entity_type: str
    entity_id: Optional[int]
    before: Optional[Dict]
    after: Optional[Dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    """Audit log list schema."""
    logs: List[AuditLogResponse]
    total: int
