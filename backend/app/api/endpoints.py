"""
Endpoint management API endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.endpoint_credential import EndpointCredential
from app.schemas.endpoint import EndpointCredentialCreate, EndpointCredentialResponse

router = APIRouter()


@router.get("/", response_model=List[EndpointCredentialResponse])
async def list_endpoints(db: AsyncSession = Depends(get_db)):
    """List all endpoint credentials."""
    
    query = select(EndpointCredential)
    result = await db.execute(query)
    endpoints = result.scalars().all()
    
    return [EndpointCredentialResponse.model_validate(endpoint) for endpoint in endpoints]


@router.post("/", response_model=EndpointCredentialResponse)
async def create_endpoint(
    endpoint_data: EndpointCredentialCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create endpoint credentials."""
    
    endpoint = EndpointCredential(**endpoint_data.model_dump())
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)
    
    return EndpointCredentialResponse.model_validate(endpoint)


@router.post("/{endpoint_id}/test")
async def test_endpoint(
    endpoint_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Test endpoint connection."""
    
    query = select(EndpointCredential).where(EndpointCredential.id == endpoint_id)
    result = await db.execute(query)
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    # TODO: Implement endpoint testing logic
    
    return {"message": "Endpoint test completed", "status": "success"}
