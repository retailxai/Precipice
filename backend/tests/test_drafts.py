"""
Draft API tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_drafts_unauthorized(client: AsyncClient):
    """Test listing drafts without authentication."""
    response = await client.get("/api/drafts")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_drafts_empty(client: AsyncClient, auth_headers):
    """Test listing drafts when none exist."""
    response = await client.get("/api/drafts", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["drafts"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_draft(client: AsyncClient, auth_headers):
    """Test creating a draft."""
    draft_data = {
        "title": "Test Draft",
        "slug": "test-draft",
        "body_md": "# Test Content",
        "summary": "A test draft",
        "tags": ["test", "example"]
    }
    
    response = await client.post(
        "/api/drafts",
        json=draft_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Draft"
    assert data["slug"] == "test-draft"
    assert data["body_md"] == "# Test Content"
    assert data["summary"] == "A test draft"
    assert data["tags"] == ["test", "example"]
    assert data["status"] == "draft"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_draft_duplicate_slug(client: AsyncClient, auth_headers):
    """Test creating draft with duplicate slug."""
    draft_data = {
        "title": "Test Draft",
        "slug": "test-draft",
        "body_md": "# Test Content"
    }
    
    # Create first draft
    await client.post("/api/drafts", json=draft_data, headers=auth_headers)
    
    # Try to create second draft with same slug
    response = await client.post(
        "/api/drafts",
        json=draft_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Slug already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_draft(client: AsyncClient, auth_headers):
    """Test getting a specific draft."""
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
    
    # Get the draft
    response = await client.get(f"/api/drafts/{draft_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Draft"
    assert data["slug"] == "test-draft"


@pytest.mark.asyncio
async def test_get_draft_not_found(client: AsyncClient, auth_headers):
    """Test getting a non-existent draft."""
    response = await client.get("/api/drafts/999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_draft(client: AsyncClient, auth_headers):
    """Test updating a draft."""
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
    
    # Update the draft
    update_data = {
        "title": "Updated Draft",
        "body_md": "# Updated Content"
    }
    
    response = await client.put(
        f"/api/drafts/{draft_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Draft"
    assert data["body_md"] == "# Updated Content"
    assert data["slug"] == "test-draft"  # Should not change


@pytest.mark.asyncio
async def test_delete_draft(client: AsyncClient, auth_headers):
    """Test deleting a draft."""
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
    
    # Delete the draft
    response = await client.delete(f"/api/drafts/{draft_id}", headers=auth_headers)
    
    assert response.status_code == 200
    assert "Draft deleted successfully" in response.json()["message"]
    
    # Verify it's deleted
    get_response = await client.get(f"/api/drafts/{draft_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_publish_draft(client: AsyncClient, auth_headers):
    """Test publishing a draft."""
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
    publish_data = {
        "endpoints": ["substack", "linkedin"]
    }
    
    response = await client.post(
        f"/api/drafts/{draft_id}/publish",
        json=publish_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "Publishing queued" in data["message"]
    assert "substack" in data["endpoints"]
    assert "linkedin" in data["endpoints"]


@pytest.mark.asyncio
async def test_draft_pagination(client: AsyncClient, auth_headers):
    """Test draft pagination."""
    # Create multiple drafts
    for i in range(5):
        draft_data = {
            "title": f"Test Draft {i}",
            "slug": f"test-draft-{i}",
            "body_md": f"# Test Content {i}"
        }
        await client.post("/api/drafts", json=draft_data, headers=auth_headers)
    
    # Test pagination
    response = await client.get("/api/drafts?page=1&size=3", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["drafts"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["size"] == 3
    assert data["pages"] == 2


@pytest.mark.asyncio
async def test_draft_search(client: AsyncClient, auth_headers):
    """Test draft search functionality."""
    # Create drafts with different content
    drafts = [
        {"title": "Python Tutorial", "slug": "python-tutorial", "body_md": "# Python content"},
        {"title": "JavaScript Guide", "slug": "js-guide", "body_md": "# JavaScript content"},
        {"title": "Web Development", "slug": "web-dev", "body_md": "# Web development content"},
    ]
    
    for draft_data in drafts:
        await client.post("/api/drafts", json=draft_data, headers=auth_headers)
    
    # Search for Python content
    response = await client.get("/api/drafts?search=Python", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["drafts"]) == 1
    assert data["drafts"][0]["title"] == "Python Tutorial"
