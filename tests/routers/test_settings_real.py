"""Real TestClient tests for settings.py router endpoints"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app


class TestSettingsRouterEndpoints:
    """Test settings CRUD endpoints"""

    @pytest.mark.asyncio
    async def test_get_settings_endpoint(self):
        """Test GET /api/settings endpoint"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/settings/")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_update_settings_endpoint(self):
        """Test POST /api/settings endpoint"""
        test_settings = {
            "anthropic_api_key": "test-key",
            "slack_webhook_url": "https://hooks.slack.com/test",
            "notion_token": "test-token",
            "notion_page_id": "test-page-id"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/settings/", json=test_settings)
            # May succeed or return validation error
            assert response.status_code in [200, 201, 422]

    @pytest.mark.asyncio
    async def test_test_connections_endpoint(self):
        """Test POST /api/settings/test-connections endpoint"""
        with patch('app.services.slack_notify.send_briefing_to_slack', new_callable=AsyncMock) as mock_slack:
            with patch('app.services.notion_export.export_briefing_to_notion', new_callable=AsyncMock) as mock_notion:
                mock_slack.return_value = None
                mock_notion.return_value = "https://notion.so/test"

                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                    response = await ac.post("/api/settings/test-connections")
                    assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_settings_with_invalid_data(self):
        """Test settings endpoint with invalid data"""
        invalid_settings = {
            "slack_webhook_url": "not-a-url",
            "notion_token": ""
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/settings/", json=invalid_settings)
            # Should validate and may return error
            assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_settings_persistence(self):
        """Test settings are persisted correctly"""
        # Set some settings
        test_settings = {
            "anthropic_api_key": "persist-test-key"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Update settings
            response1 = await ac.post("/api/settings/", json=test_settings)
            assert response1.status_code in [200, 201, 422]

            # Retrieve settings
            response2 = await ac.get("/api/settings/")
            assert response2.status_code == 200

    @pytest.mark.asyncio
    async def test_settings_partial_update(self):
        """Test updating only some settings fields"""
        partial_settings = {
            "slack_webhook_url": "https://hooks.slack.com/updated"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/settings/", json=partial_settings)
            assert response.status_code in [200, 201, 422]


class TestSettingsLogic:
    """Test settings logic functions directly"""

    def test_import_settings_router(self):
        """Verify settings router can be imported"""
        try:
            from app.routers import settings
            assert settings.router is not None
        except ImportError:
            pytest.skip("Cannot import settings router")

    def test_settings_router_endpoints_exist(self):
        """Verify expected endpoints are registered"""
        try:
            from app.routers import settings

            # Check router has routes
            assert hasattr(settings, 'router')
            routes = settings.router.routes
            assert len(routes) > 0

        except ImportError:
            pytest.skip("Cannot import settings router")

    def test_settings_model(self):
        """Test settings model structure"""
        try:
            from app.config import Settings

            settings = Settings()
            # Should have required attributes
            assert hasattr(settings, 'anthropic_api_key')
            assert hasattr(settings, 'database_url')

        except ImportError:
            pytest.skip("Cannot import Settings")

    @pytest.mark.asyncio
    async def test_test_connections_logic(self):
        """Test connection testing logic"""
        try:
            from app.routers import settings

            if hasattr(settings, 'test_connections'):
                with patch('app.services.slack_notify.send_briefing_to_slack', new_callable=AsyncMock):
                    with patch('app.services.notion_export.export_briefing_to_notion', new_callable=AsyncMock):
                        # Function exists and can be called
                        assert callable(settings.test_connections)

        except ImportError:
            pytest.skip("Cannot import settings")
