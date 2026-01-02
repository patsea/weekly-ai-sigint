"""Tests for Scheduler API."""
import pytest
from httpx import AsyncClient


class TestSchedulerAPI:
    """Test scheduler operations."""

    async def test_get_scheduler_status(self, client: AsyncClient):
        """Test getting scheduler status."""
        response = await client.get("/api/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "paused" in data
        assert "next_run" in data

    async def test_pause_scheduler(self, client: AsyncClient):
        """Test pausing scheduler."""
        response = await client.post("/api/scheduler/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_resume_scheduler(self, client: AsyncClient):
        """Test resuming scheduler."""
        response = await client.post("/api/scheduler/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_get_history(self, client: AsyncClient):
        """Test getting job history."""
        response = await client.get("/api/scheduler/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "count" in data
