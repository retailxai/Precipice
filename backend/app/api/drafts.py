"""
Draft API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.rbac import require_draft_read, require_draft_write, require_draft_publish
from app.models.draft import Draft
from app.schemas.draft import (
    DraftCreate,
    DraftUpdate,
    DraftResponse,
    DraftList,
    DraftAnalyzeRequest,
    DraftAIRequest,
    DraftPreviewRequest,
    DraftPublishRequest,
)

router = APIRouter()


@router.get("/", response_model=DraftList)
async def list_drafts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_draft_read),
):
    """List drafts with pagination and filtering."""
    
    # Build query
    query = select(Draft).options(selectinload(Draft.publish_records))
    
    # Apply filters
    if status:
        query = query.where(Draft.status == status)
    
    if search:
        query = query.where(
            Draft.title.ilike(f"%{search}%") |
            Draft.summary.ilike(f"%{search}%") |
            Draft.body_md.ilike(f"%{search}%")
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.order_by(desc(Draft.updated_at)).offset((page - 1) * size).limit(size)
    
    # Execute query
    result = await db.execute(query)
    drafts = result.scalars().all()
    
    # Convert to response format
    draft_responses = [DraftResponse.model_validate(draft) for draft in drafts]
    
    return DraftList(
        drafts=draft_responses,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_draft_read),
):
    """Get a specific draft by ID."""
    
    query = select(Draft).where(Draft.id == draft_id).options(selectinload(Draft.publish_records))
    result = await db.execute(query)
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return DraftResponse.model_validate(draft)


@router.post("/", response_model=DraftResponse)
async def create_draft(
    draft_data: DraftCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_draft_write),
):
    """Create a new draft."""
    
    # Check if slug already exists
    existing_query = select(Draft).where(Draft.slug == draft_data.slug)
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already exists")
    
    # Create draft
    draft = Draft(**draft_data.model_dump())
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    
    return DraftResponse.model_validate(draft)


@router.put("/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: int,
    draft_data: DraftUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_draft_write),
):
    """Update a draft."""
    
    query = select(Draft).where(Draft.id == draft_id)
    result = await db.execute(query)
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Update fields
    update_data = draft_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(draft, field, value)
    
    await db.commit()
    await db.refresh(draft)
    
    return DraftResponse.model_validate(draft)


@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_draft_write),
):
    """Delete a draft."""
    
    query = select(Draft).where(Draft.id == draft_id)
    result = await db.execute(query)
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    await db.delete(draft)
    await db.commit()
    
    return {"message": "Draft deleted successfully"}


@router.post("/{draft_id}/analyze")
async def analyze_draft(
    draft_id: int,
    request: DraftAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze a draft."""
    
    # Get draft
    query = select(Draft).where(Draft.id == draft_id)
    result = await db.execute(query)
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # TODO: Implement analysis logic
    # This would typically enqueue a job for analysis
    
    return {"message": "Analysis queued", "analysis_type": request.analysis_type}


@router.post("/{draft_id}/ai")
async def ai_improve_draft(
    draft_id: int,
    request: DraftAIRequest,
    db: AsyncSession = Depends(get_db),
):
    """Use AI to improve a draft."""
    
    # Get draft
    query = select(Draft).where(Draft.id == draft_id)
    result = await db.execute(query)
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # TODO: Implement AI improvement logic
    # This would typically enqueue a job for AI processing
    
    return {"message": "AI improvement queued", "action": request.action}


@router.post("/{draft_id}/preview")
async def preview_draft(
    draft_id: int,
    request: DraftPreviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Preview a draft for a specific endpoint."""
    
    # Get draft
    query = select(Draft).where(Draft.id == draft_id)
    result = await db.execute(query)
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # TODO: Implement preview logic
    # This would format the draft for the specific endpoint
    
    return {
        "message": "Preview generated",
        "endpoint": request.endpoint,
        "preview": "Preview content would be here",
    }


@router.post("/{draft_id}/publish")
async def publish_draft(
    draft_id: int,
    request: DraftPublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_draft_publish),
):
    """Publish a draft to specified endpoints."""
    
    # Get draft
    query = select(Draft).where(Draft.id == draft_id)
    result = await db.execute(query)
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # TODO: Implement publishing logic
    # This would enqueue jobs for each endpoint
    
    return {
        "message": "Publishing queued",
        "endpoints": request.endpoints,
        "job_ids": ["job_1", "job_2"],  # Placeholder
    }
