"""Tests for Sources API."""
import pytest
from httpx import AsyncClient


class TestSourcesAPI:
    """Test source CRUD operations."""

    async def test_list_sources_empty(self, client: AsyncClient):
        """Test listing sources when none exist."""
        response = await client.get("/api/sources/")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_sources_with_data(self, client: AsyncClient, sample_source):
        """Test listing sources with data."""
        response = await client.get("/api/sources/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Newsletter"

    async def test_create_source(self, client: AsyncClient):
        """Test creating a new source."""
        payload = {
            "name": "New Source",
            "category": "newsletter",
            "source_type": "rss",
            "url": "https://new.example.com/feed",
            "priority": 7,
            "active": True,
        }
        response = await client.post("/api/sources/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Source"
        assert data["id"] is not None

    async def test_create_source_validation_error(self, client: AsyncClient):
        """Test creating source with invalid data."""
        payload = {"name": ""}  # Missing required fields
        response = await client.post("/api/sources/", json=payload)
        assert response.status_code == 422

    async def test_get_source_by_id(self, client: AsyncClient, sample_source):
        """Test getting a single source."""
        response = await client.get(f"/api/sources/{sample_source.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Newsletter"

    async def test_get_source_not_found(self, client: AsyncClient):
        """Test getting non-existent source."""
        response = await client.get("/api/sources/99999")
        assert response.status_code == 404

    async def test_update_source(self, client: AsyncClient, sample_source):
        """Test updating a source."""
        payload = {"priority": 10}
        response = await client.patch(f"/api/sources/{sample_source.id}", json=payload)
        assert response.status_code == 200
        assert response.json()["priority"] == 10

    async def test_delete_source(self, client: AsyncClient, sample_source):
        """Test deleting a source."""
        response = await client.delete(f"/api/sources/{sample_source.id}")
        assert response.status_code == 204

        # Verify deleted
        response = await client.get(f"/api/sources/{sample_source.id}")
        assert response.status_code == 404

    async def test_delete_source_not_found(self, client: AsyncClient):
        """Test deleting non-existent source."""
        response = await client.delete("/api/sources/99999")
        assert response.status_code == 404
