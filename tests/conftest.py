"""Pytest fixtures for Weekly AI Sigint tests."""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.database import Base, get_session
from app.models.source import Source
from app.models.content import ContentItem
from app.models.briefing import Briefing


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with overridden database."""

    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_source(test_session) -> Source:
    """Create a sample source for testing."""
    source = Source(
        name="Test Newsletter",
        category="newsletter",
        source_type="rss",
        url="https://test.example.com/feed",
        priority=5,
        active=True,
    )
    test_session.add(source)
    await test_session.commit()
    await test_session.refresh(source)
    return source


@pytest.fixture
async def sample_content(test_session, sample_source) -> ContentItem:
    """Create sample content for testing."""
    from datetime import datetime

    content = ContentItem(
        source_id=sample_source.id,
        title="Test Article",
        url="https://test.example.com/article-1",
        content="This is test content for the article.",
        published_at=datetime.utcnow(),
    )
    test_session.add(content)
    await test_session.commit()
    await test_session.refresh(content)
    return content


@pytest.fixture
async def sample_briefing(test_session) -> Briefing:
    """Create a sample briefing for testing."""
    from datetime import datetime, timedelta

    briefing = Briefing(
        title="Weekly AI Sigint - Test",
        content="# Test Briefing\n\nThis is a test briefing content.",
        week_start=datetime.utcnow() - timedelta(days=7),
        week_end=datetime.utcnow(),
    )
    test_session.add(briefing)
    await test_session.commit()
    await test_session.refresh(briefing)
    return briefing
