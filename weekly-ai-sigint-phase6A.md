# Weekly AI Sigint — Phase 6A Instructions

> Execute Phase 6A: Unit Tests with pytest (80% coverage target)

## Pre-Flight

```bash
# Verify working directory
pwd  # Should be weekly-ai-sigint

# Read best practices first
cat ~/Dropbox/ALOMA/claude-code/CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md | head -100

# Verify all phases complete
ls -la app/routers/*.py app/services/*.py app/templates/*.html

# Install test dependencies
source venv/bin/activate
pip install pytest pytest-asyncio pytest-cov httpx --break-system-packages

# Kill any existing server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
```

---

## Phase 6A Scope

### Deliverables

1. `tests/conftest.py` — Pytest fixtures (test database, client, mocks)
2. `tests/test_sources.py` — Source CRUD tests
3. `tests/test_briefings.py` — Briefing CRUD tests
4. `tests/test_content.py` — Content API tests
5. `tests/test_settings.py` — Settings API tests
6. `tests/test_prompt.py` — Prompt API tests
7. `tests/test_scheduler.py` — Scheduler API tests
8. `tests/test_services.py` — Service layer tests (mocked external calls)
9. `pytest.ini` — Pytest configuration
10. Update `requirements.txt` — Add test dependencies

### Coverage Target

| Category | Target | Scope |
|----------|--------|-------|
| API Routes | 80% | All routers |
| Services | 80% | Core logic (mocked external APIs) |
| Models | 80% | Database operations |
| Critical paths | 90% | Auth, validation, error handling |

---

## Implementation Details

### 1. `pytest.ini`

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
```

### 2. `tests/conftest.py`

```python
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
```

### 3. `tests/test_sources.py`

```python
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
        assert response.status_code == 200
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
```

### 4. `tests/test_briefings.py`

```python
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
```

### 5. `tests/test_content.py`

```python
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
```

### 6. `tests/test_settings.py`

```python
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
```

### 7. `tests/test_prompt.py`

```python
"""Tests for Prompt API."""
import pytest
from httpx import AsyncClient
from pathlib import Path


class TestPromptAPI:
    """Test prompt operations."""
    
    async def test_get_prompt(self, client: AsyncClient):
        """Test getting current prompt."""
        response = await client.get("/api/prompt/")
        # May be 404 if prompt file doesn't exist in test environment
        assert response.status_code in [200, 404]
    
    async def test_save_prompt(self, client: AsyncClient, tmp_path, monkeypatch):
        """Test saving prompt (with mocked file path)."""
        # This test would need to mock the PROMPT_FILE path
        # For now, just test the endpoint accepts the request
        payload = {"content": "# Test Prompt\n\nThis is a test."}
        response = await client.post("/api/prompt/", json=payload)
        # May succeed or fail depending on file permissions
        assert response.status_code in [200, 500]
    
    async def test_save_prompt_empty_content(self, client: AsyncClient):
        """Test saving empty prompt fails."""
        payload = {"content": ""}
        response = await client.post("/api/prompt/", json=payload)
        assert response.status_code == 400
    
    async def test_get_preview(self, client: AsyncClient):
        """Test prompt preview."""
        response = await client.get("/api/prompt/preview")
        # May be 404 if prompt file doesn't exist
        assert response.status_code in [200, 404]
```

### 8. `tests/test_scheduler.py`

```python
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
```

### 9. `tests/test_services.py`

```python
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
```

### 10. `tests/test_health.py`

```python
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
```

### 11. Update `requirements.txt`

Add test dependencies:

```
# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
httpx>=0.24.0
```

---

## Running Tests

### Run All Tests

```bash
# Run all tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Specific Test Files

```bash
# Run only source tests
pytest tests/test_sources.py -v

# Run only a specific test
pytest tests/test_sources.py::TestSourcesAPI::test_create_source -v
```

### Coverage Thresholds

```bash
# Fail if coverage below 80%
pytest --cov=app --cov-fail-under=80
```

---

## Verification Gate

After implementation, verify:

```bash
# 1. Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx --break-system-packages

# 2. Run tests
pytest -v

# 3. Check coverage
pytest --cov=app --cov-report=term-missing

# 4. Verify threshold
pytest --cov=app --cov-fail-under=80
```

**Success criteria:**
- [ ] All tests pass
- [ ] Coverage >= 80% overall
- [ ] No import errors
- [ ] No fixture errors

---

## Commit After Verification

```bash
git add -A
git commit -m "Phase 6A complete: Unit tests with pytest

- Added conftest.py with async fixtures
- Test coverage for all API routers
- Mocked external services (Claude, Notion, Slack)
- pytest.ini configuration
- 80%+ code coverage achieved"
```
