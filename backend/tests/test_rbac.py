"""
RBAC (Role-Based Access Control) tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_viewer_can_read_drafts(client: AsyncClient, db_session):
    """Test that viewers can read drafts."""
    from app.api.auth import get_password_hash
    from app.models.user import User, UserRole
    
    # Create a viewer user
    viewer = User(
        username="viewer",
        email="viewer@example.com",
        hashed_password=get_password_hash("viewerpassword"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db_session.add(viewer)
    await db_session.commit()
    
    # Login as viewer
    response = await client.post(
        "/api/auth/token",
        data={"username": "viewer", "password": "viewerpassword"}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to read drafts
    response = await client.get("/api/drafts", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_viewer_cannot_create_drafts(client: AsyncClient, db_session):
    """Test that viewers cannot create drafts."""
    from app.api.auth import get_password_hash
    from app.models.user import User, UserRole
    
    # Create a viewer user
    viewer = User(
        username="viewer",
        email="viewer@example.com",
        hashed_password=get_password_hash("viewerpassword"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db_session.add(viewer)
    await db_session.commit()
    
    # Login as viewer
    response = await client.post(
        "/api/auth/token",
        data={"username": "viewer", "password": "viewerpassword"}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to create a draft
    draft_data = {
        "title": "Test Draft",
        "slug": "test-draft",
        "body_md": "# Test Content"
    }
    
    response = await client.post("/api/drafts", json=draft_data, headers=headers)
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_editor_can_create_drafts(client: AsyncClient, auth_headers):
    """Test that editors can create drafts."""
    draft_data = {
        "title": "Test Draft",
        "slug": "test-draft",
        "body_md": "# Test Content"
    }
    
    response = await client.post("/api/drafts", json=draft_data, headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_editor_can_publish_drafts(client: AsyncClient, auth_headers):
    """Test that editors can publish drafts."""
    # Create a draft first
    draft_data = {
        "title": "Test Draft",
        "slug": "test-draft",
        "body_md": "# Test Content"
    }
    
    create_response = await client.post(
        "/api/drafts",
        json=draft_data,
        headers=auth_headers
    )
    draft_id = create_response.json()["id"]
    
    # Publish the draft
    publish_data = {"endpoints": ["substack"]}
    response = await client.post(
        f"/api/drafts/{draft_id}/publish",
        json=publish_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_can_access_all_endpoints(client: AsyncClient, admin_auth_headers):
    """Test that admins can access all endpoints."""
    # Test health endpoint
    response = await client.get("/api/health/summary", headers=admin_auth_headers)
    assert response.status_code == 200
    
    # Test jobs endpoint
    response = await client.get("/api/jobs", headers=admin_auth_headers)
    assert response.status_code == 200
    
    # Test settings endpoint
    response = await client.get("/api/settings/feature-flags", headers=admin_auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test that unauthenticated users cannot access protected endpoints."""
    # Test drafts endpoint
    response = await client.get("/api/drafts")
    assert response.status_code == 401
    
    # Test health endpoint
    response = await client.get("/api/health/summary")
    assert response.status_code == 401
    
    # Test jobs endpoint
    response = await client.get("/api/jobs")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient):
    """Test access with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    
    response = await client.get("/api/drafts", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_token(client: AsyncClient):
    """Test access with expired token."""
    # This would require mocking JWT token expiration
    # For now, we'll test with a malformed token
    headers = {"Authorization": "Bearer expired.token.here"}
    
    response = await client.get("/api/drafts", headers=headers)
    assert response.status_code == 401
