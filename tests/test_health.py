"""Tests for health and root endpoints."""
import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health and basic endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test health endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "scheduler" in data

    async def test_root_page(self, client: AsyncClient):
        """Test root page loads."""
        response = await client.get("/")
        assert response.status_code == 200
        assert b"Weekly AI Sigint" in response.content or b"Dashboard" in response.content
