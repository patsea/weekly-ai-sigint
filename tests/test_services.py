"""Tests for service layer (with mocked external APIs)."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


class TestFetcherService:
    """Test fetcher service with mocked HTTP calls."""

    @pytest.mark.asyncio
    async def test_fetch_rss_source(self, test_session, sample_source):
        """Test fetching from RSS source (mocked)."""
        # This would mock the actual HTTP call
        # and verify the service correctly parses RSS
        pass  # Placeholder for actual implementation


class TestSynthesizerService:
    """Test synthesizer service with mocked Claude API."""

    @pytest.mark.asyncio
    async def test_synthesize_briefing(self, test_session, sample_content):
        """Test briefing synthesis with mocked Claude."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            # Mock Claude response
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.return_value = MagicMock(
                content=[MagicMock(text="# Mocked Briefing\n\nTest content.")]
            )

            # Test would call synthesize_briefing and verify result
            pass  # Placeholder for actual implementation


class TestNotionExportService:
    """Test Notion export with mocked API."""

    @pytest.mark.asyncio
    async def test_export_to_notion(self, test_session, sample_briefing):
        """Test Notion export with mocked client."""
        with patch('notion_client.Client') as mock_notion:
            mock_client = MagicMock()
            mock_notion.return_value = mock_client
            mock_client.pages.create.return_value = {
                "id": "mock-page-id",
                "url": "https://notion.so/mock-page",
            }

            # Test would call export service and verify
            pass  # Placeholder for actual implementation


class TestSlackNotifyService:
    """Test Slack notification with mocked webhook."""

    @pytest.mark.asyncio
    async def test_send_slack_notification(self, test_session, sample_briefing):
        """Test Slack notification with mocked httpx."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(status_code=200)

            # Test would call notify service and verify
            pass  # Placeholder for actual implementation
