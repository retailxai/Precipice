"""
Settings management API endpoints
"""

from typing import Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.feature_flag import FeatureFlag

router = APIRouter()


@router.get("/feature-flags")
async def get_feature_flags(db: AsyncSession = Depends(get_db)):
    """Get all feature flags."""
    
    query = select(FeatureFlag)
    result = await db.execute(query)
    flags = result.scalars().all()
    
    return {flag.key: {"enabled": flag.enabled, "payload": flag.payload} for flag in flags}


@router.put("/feature-flags/{key}")
async def update_feature_flag(
    key: str,
    enabled: bool,
    payload: Dict = None,
    db: AsyncSession = Depends(get_db),
):
    """Update a feature flag."""
    
    query = select(FeatureFlag).where(FeatureFlag.key == key)
    result = await db.execute(query)
    flag = result.scalar_one_or_none()
    
    if not flag:
        flag = FeatureFlag(key=key, enabled=enabled, payload=payload or {})
        db.add(flag)
    else:
        flag.enabled = enabled
        if payload is not None:
            flag.payload = payload
    
    await db.commit()
    
    return {"message": "Feature flag updated"}
