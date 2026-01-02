"""Tests for Settings API."""
import pytest
from httpx import AsyncClient


class TestSettingsAPI:
    """Test settings operations."""

    async def test_get_settings(self, client: AsyncClient):
        """Test getting current settings."""
        response = await client.get("/api/settings/")
        assert response.status_code == 200
        data = response.json()
        # Should have masked values
        assert "anthropic_api_key" in data

    async def test_test_connections(self, client: AsyncClient):
        """Test connection validation endpoint."""
        response = await client.post("/api/settings/test-connections")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "anthropic" in data["results"]
        assert "notion" in data["results"]
        assert "slack" in data["results"]
