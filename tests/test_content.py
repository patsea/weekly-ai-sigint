"""Tests for Content API."""
import pytest
from httpx import AsyncClient


class TestContentAPI:
    """Test content operations."""

    async def test_list_content_empty(self, client: AsyncClient):
        """Test listing content when none exists."""
        response = await client.get("/api/content/")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_content_with_data(self, client: AsyncClient, sample_content):
        """Test listing content with data."""
        response = await client.get("/api/content/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_list_content_with_limit(self, client: AsyncClient, sample_content):
        """Test listing content with limit parameter."""
        response = await client.get("/api/content/?limit=5")
        assert response.status_code == 200
