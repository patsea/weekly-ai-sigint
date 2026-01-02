"""Tests for Briefings API."""
import pytest
from httpx import AsyncClient


class TestBriefingsAPI:
    """Test briefing operations."""

    async def test_list_briefings_empty(self, client: AsyncClient):
        """Test listing briefings when none exist."""
        response = await client.get("/api/briefings/")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_briefings_with_data(self, client: AsyncClient, sample_briefing):
        """Test listing briefings with data."""
        response = await client.get("/api/briefings/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Test" in data[0]["title"]

    async def test_get_latest_briefing(self, client: AsyncClient, sample_briefing):
        """Test getting latest briefing."""
        response = await client.get("/api/briefings/latest")
        assert response.status_code == 200
        assert response.json()["id"] == sample_briefing.id

    async def test_get_latest_briefing_none(self, client: AsyncClient):
        """Test getting latest when none exist."""
        response = await client.get("/api/briefings/latest")
        assert response.status_code == 404

    async def test_get_briefing_by_id(self, client: AsyncClient, sample_briefing):
        """Test getting briefing by ID."""
        response = await client.get(f"/api/briefings/{sample_briefing.id}")
        assert response.status_code == 200
        assert response.json()["content"] is not None

    async def test_get_briefing_not_found(self, client: AsyncClient):
        """Test getting non-existent briefing."""
        response = await client.get("/api/briefings/99999")
        assert response.status_code == 404

    async def test_delete_briefing(self, client: AsyncClient, sample_briefing):
        """Test deleting a briefing."""
        response = await client.delete(f"/api/briefings/{sample_briefing.id}")
        assert response.status_code in [200, 204]

        # Verify deleted
        response = await client.get(f"/api/briefings/{sample_briefing.id}")
        assert response.status_code == 404
