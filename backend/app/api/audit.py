"""
Audit log API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse, AuditLogList

router = APIRouter()


@router.get("/", response_model=AuditLogList)
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    actor: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs with filtering."""
    
    query = select(AuditLog)
    
    # Apply filters
    if actor:
        query = query.where(AuditLog.actor == actor)
    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    
    query = query.order_by(desc(AuditLog.created_at)).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    log_responses = [AuditLogResponse.model_validate(log) for log in logs]
    
    return AuditLogList(logs=log_responses, total=len(log_responses))
