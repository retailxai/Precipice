"""
Job management API endpoints
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import JobResponse, JobList

router = APIRouter()


@router.get("/", response_model=JobList)
async def list_jobs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List recent jobs."""
    
    query = select(Job).order_by(desc(Job.queued_at)).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    job_responses = [JobResponse.model_validate(job) for job in jobs]
    
    return JobList(jobs=job_responses, total=len(job_responses))


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific job by ID."""
    
    query = select(Job).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse.model_validate(job)


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retry a failed job."""
    query = select(Job).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Only allow retry for FAILED or CANCELLED jobs; otherwise 400
    if job.status not in {JobStatus.FAILED, JobStatus.CANCELLED}:
        raise HTTPException(status_code=400, detail="Only failed or cancelled jobs can be retried")

    # Minimal viable retry behavior: requeue by resetting status and timestamps
    job.status = JobStatus.PENDING
    job.queued_at = datetime.utcnow()
    job.started_at = None
    job.finished_at = None
    job.error_text = None
    job.attempts = (job.attempts or 0) + 1

    await db.commit()
    await db.refresh(job)

    return {"message": "Job retry queued", "id": job.id, "attempts": job.attempts}
