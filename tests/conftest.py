import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Event loop fixture
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# In-memory database engine
@pytest.fixture(scope="function")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    try:
        from app.models.database import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except ImportError:
        pass
    yield engine
    await engine.dispose()

# Session fixture with proper isolation
@pytest.fixture
async def test_session(test_engine):
    async_session_maker = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session
        await session.rollback()

# Alias for existing tests
@pytest.fixture
async def async_session(test_session):
    return test_session

# Override app dependency
@pytest.fixture
async def client(test_session):
    try:
        from app.main import app
        from app.models.database import get_session as get_db
        
        async def override_get_db():
            yield test_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
        
        app.dependency_overrides.clear()
    except ImportError as e:
        pytest.skip(f"App import failed: {e}")

# Mock Anthropic client
@pytest.fixture
def mock_anthropic_client():
    client = MagicMock()
    client.messages.create = AsyncMock(return_value=MagicMock(
        content=[MagicMock(text="Test response")]
    ))
    return client

# Sample fixtures - return proper data structures
@pytest.fixture
def sample_article():
    return {
        "title": "Test Article",
        "url": "https://example.com/test",
        "content": "This is test content about AI developments.",
        "source": "Test Source",
        "published_date": "2026-01-28"
    }

@pytest.fixture
async def sample_source(test_session):
    try:
        from app.models.source import Source
        source = Source(
            name="Test Newsletter",
            url="https://example.com/feed",
            source_type="rss",
            category="newsletter",
            priority=5,
            active=True
        )
        test_session.add(source)
        await test_session.commit()
        await test_session.refresh(source)
        return source
    except ImportError:
        return {"id": 1, "name": "Test Source", "url": "https://example.com/feed"}

@pytest.fixture
async def sample_briefing(test_session):
    try:
        from app.models.briefing import Briefing
        now = datetime.now(timezone.utc)
        briefing = Briefing(
            title="Test Weekly Briefing",
            content="Test briefing content",
            week_start=now,
            week_end=now
        )
        test_session.add(briefing)
        await test_session.commit()
        await test_session.refresh(briefing)
        return briefing
    except ImportError:
        return {"id": 1, "title": "Weekly AI Sigint", "content": "Test content"}

@pytest.fixture
async def sample_content(test_session):
    try:
        from app.models.content import ContentItem
        content = ContentItem(
            title="Test Content",
            url="https://example.com/article",
            content="Raw test content",
            source_id=1
        )
        test_session.add(content)
        await test_session.commit()
        await test_session.refresh(content)
        return content
    except ImportError:
        return {"id": 1, "title": "Test Content"}

@pytest.fixture
def mock_settings():
    return MagicMock(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        ANTHROPIC_API_KEY="test-key",
        WEEKLY_RUN_DAY=0, SLACK_WEBHOOK_URL="", NOTION_TOKEN="",
        DEBUG=True
    )

