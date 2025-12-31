# Weekly AI Sigint — MVP Technical Proposal

> A locally-hosted web application that autonomously fetches content from curated AI/enterprise tech sources, synthesizes weekly intelligence briefings using Claude, stores historical data for analysis, exports to Notion, and notifies via Slack.

**Project Name**: `weekly-ai-sigint`  
**Version**: 1.0  
**Date**: December 2025  
**Author**: Claude (for Patrick Williamson)  
**Estimated Build Time**: 3-5 days with Claude Code

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Data Models](#3-data-models)
4. [API Design](#4-api-design)
5. [UI Wireframes](#5-ui-wireframes)
6. [Phase-Based Build Plan](#6-phase-based-build-plan)
7. [CLAUDE.md Template](#7-claudemd-template)
8. [Known Pitfalls & Mitigations](#8-known-pitfalls--mitigations)
9. [File Manifest](#9-file-manifest)
10. [Future Enhancements (Post-MVP)](#10-future-enhancements-post-mvp)

---

## 1. Executive Summary

### Problem
Manually tracking 100+ AI/enterprise tech sources weekly is time-consuming and error-prone. The current "Sunday Routine" requires 90 minutes of manual aggregation with no historical analysis capability.

### Solution
An automated pipeline that:
1. **Fetches** content from RSS feeds, APIs, and web sources on a configurable schedule
2. **Stores** raw content and processed briefings in SQLite for historical analysis
3. **Synthesizes** a structured briefing using Claude API with your custom prompt template
4. **Exports** the final briefing to a Notion page
5. **Notifies** via Slack webhook with top 5 trending items

### MVP Scope Boundaries

| In Scope | Out of Scope |
|----------|--------------|
| RSS feed fetching | Real-time monitoring |
| Basic web scraping (public pages) | Paywalled content auto-access |
| Claude API synthesis | Multi-user authentication |
| SQLite storage | Advanced analytics dashboard |
| Notion export | Email delivery |
| Slack notification | Mobile app |
| Config UI (watchlist, credentials, prompt) | Custom ML models |
| Weekly scheduled runs | Sub-daily scheduling |

---

## 2. Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WEEKLY AI SIGINT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │   SCHEDULER  │────▶│   FETCHER    │────▶│   STORAGE    │                │
│  │  (APScheduler)│     │  (feedparser │     │   (SQLite)   │                │
│  │              │     │   + httpx)   │     │              │                │
│  └──────────────┘     └──────────────┘     └──────┬───────┘                │
│         │                                         │                         │
│         │              ┌──────────────┐           │                         │
│         └─────────────▶│  SYNTHESIZER │◀──────────┘                         │
│                        │ (Claude API) │                                     │
│                        └──────┬───────┘                                     │
│                               │                                             │
│         ┌─────────────────────┼─────────────────────┐                       │
│         │                     │                     │                       │
│         ▼                     ▼                     ▼                       │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │    NOTION    │     │    SLACK     │     │   STORAGE    │                │
│  │   EXPORTER   │     │   NOTIFIER   │     │  (briefings) │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           CONFIG UI (FastAPI + HTML/Tailwind)               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Watchlist  │  │ Credentials│  │   Prompt   │  │  Schedule  │            │
│  │   Editor   │  │   Manager  │  │   Editor   │  │   Config   │            │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Scheduler** | APScheduler | Triggers weekly fetch + synthesis pipeline |
| **Fetcher** | feedparser, httpx, BeautifulSoup | Pulls content from RSS, APIs, web pages |
| **Storage** | SQLite + SQLAlchemy | Persists raw content, processed briefings, config |
| **Synthesizer** | Anthropic Python SDK | Sends content to Claude, receives structured briefing |
| **Notion Exporter** | notion-client | Pushes markdown briefing to specified Notion page |
| **Slack Notifier** | httpx (webhook) | Posts top 5 items notification |
| **Config UI** | FastAPI + Jinja2 + Tailwind | Web interface for configuration |

### Directory Structure

```
weekly-ai-sigint/
├── CLAUDE.md                    # Project instructions for Claude Code
├── README.md                    # User documentation
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── .env                         # Local environment (gitignored)
├── .gitignore
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Settings and environment loading
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── source.py            # Source/watchlist models
│   │   ├── content.py           # Fetched content models
│   │   └── briefing.py          # Briefing output models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── fetcher.py           # Content fetching logic
│   │   ├── synthesizer.py       # Claude API integration
│   │   ├── notion_export.py     # Notion API integration
│   │   ├── slack_notify.py      # Slack webhook integration
│   │   └── scheduler.py         # APScheduler setup
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── sources.py           # Watchlist CRUD endpoints
│   │   ├── briefings.py         # Briefing endpoints
│   │   ├── settings.py          # Credentials/config endpoints
│   │   └── manual.py            # Manual trigger endpoints
│   │
│   ├── templates/
│   │   ├── base.html            # Base template with Tailwind
│   │   ├── index.html           # Dashboard
│   │   ├── sources.html         # Watchlist editor
│   │   ├── settings.html        # Credentials manager
│   │   ├── prompt.html          # Prompt template editor
│   │   └── briefings.html       # Briefing history viewer
│   │
│   └── static/
│       └── css/
│           └── custom.css       # Minimal custom styles
│
├── data/
│   └── briefings.db             # SQLite database (gitignored)
│
├── prompts/
│   └── sunday_briefing.md       # Default prompt template
│
└── tests/
    ├── __init__.py
    ├── test_fetcher.py
    ├── test_synthesizer.py
    └── test_exports.py
```

---

## 3. Data Models

### SQLite Schema

```sql
-- Sources: The watchlist items
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'person', 'org', 'newsletter', 'podcast', 'research', 'event'
    source_type TEXT NOT NULL,  -- 'rss', 'api', 'web', 'manual'
    url TEXT NOT NULL,
    secondary_url TEXT,
    description TEXT,
    priority INTEGER DEFAULT 5,  -- 1-10 scale
    is_active BOOLEAN DEFAULT TRUE,
    fetch_frequency TEXT DEFAULT 'weekly',  -- 'daily', 'weekly', 'manual'
    last_fetched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content: Raw fetched items
CREATE TABLE content_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    external_id TEXT,  -- GUID, URL hash, etc. for deduplication
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    url TEXT,
    author TEXT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT,  -- JSON array
    metadata TEXT,  -- JSON object for source-specific data
    FOREIGN KEY (source_id) REFERENCES sources(id),
    UNIQUE(source_id, external_id)
);

-- Briefings: Synthesized outputs
CREATE TABLE briefings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    executive_summary TEXT,
    full_content TEXT NOT NULL,  -- Full markdown
    content_item_count INTEGER,
    source_count INTEGER,
    topics TEXT,  -- JSON array of detected topics
    people_mentioned TEXT,  -- JSON array
    orgs_mentioned TEXT,  -- JSON array
    notion_page_id TEXT,
    notion_url TEXT,
    slack_notified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT  -- JSON: token counts, model used, etc.
);

-- Briefing-Content junction for traceability
CREATE TABLE briefing_sources (
    briefing_id INTEGER NOT NULL,
    content_item_id INTEGER NOT NULL,
    relevance_score REAL,  -- Optional: how relevant this item was
    section TEXT,  -- Which briefing section used this item
    PRIMARY KEY (briefing_id, content_item_id),
    FOREIGN KEY (briefing_id) REFERENCES briefings(id),
    FOREIGN KEY (content_item_id) REFERENCES content_items(id)
);

-- Credentials: Encrypted storage for API keys
CREATE TABLE credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT NOT NULL UNIQUE,  -- 'anthropic', 'notion', 'slack', etc.
    key_name TEXT NOT NULL,
    encrypted_value TEXT NOT NULL,  -- Fernet encrypted
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Config: Application settings
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_content_source ON content_items(source_id);
CREATE INDEX idx_content_published ON content_items(published_at);
CREATE INDEX idx_content_fetched ON content_items(fetched_at);
CREATE INDEX idx_briefing_week ON briefings(week_start, week_end);
CREATE INDEX idx_sources_category ON sources(category);
CREATE INDEX idx_sources_active ON sources(is_active);
```

### SQLAlchemy Models (Python)

```python
# app/models/source.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # person, org, newsletter, etc.
    source_type = Column(String, nullable=False)  # rss, api, web, manual
    url = Column(String, nullable=False)
    secondary_url = Column(String)
    description = Column(Text)
    priority = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    fetch_frequency = Column(String, default="weekly")
    last_fetched_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

---

## 4. API Design

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Sources** |||
| GET | `/api/sources` | List all sources (filterable by category, active) |
| POST | `/api/sources` | Add new source |
| GET | `/api/sources/{id}` | Get source details |
| PUT | `/api/sources/{id}` | Update source |
| DELETE | `/api/sources/{id}` | Remove source |
| POST | `/api/sources/import` | Bulk import from JSON/CSV |
| **Content** |||
| GET | `/api/content` | List fetched content (filterable by date, source) |
| GET | `/api/content/{id}` | Get content item details |
| DELETE | `/api/content/before/{date}` | Prune old content |
| **Briefings** |||
| GET | `/api/briefings` | List all briefings |
| GET | `/api/briefings/{id}` | Get briefing details |
| GET | `/api/briefings/latest` | Get most recent briefing |
| DELETE | `/api/briefings/{id}` | Delete briefing |
| **Manual Triggers** |||
| POST | `/api/run/fetch` | Trigger content fetch now |
| POST | `/api/run/synthesize` | Trigger briefing synthesis |
| POST | `/api/run/export/notion` | Export latest to Notion |
| POST | `/api/run/notify/slack` | Send Slack notification |
| POST | `/api/run/full-pipeline` | Run complete pipeline |
| **Settings** |||
| GET | `/api/settings` | Get all settings |
| PUT | `/api/settings/{key}` | Update setting |
| GET | `/api/credentials` | List credential services (not values) |
| POST | `/api/credentials` | Add/update credential |
| DELETE | `/api/credentials/{service}` | Remove credential |
| GET | `/api/prompt` | Get current prompt template |
| PUT | `/api/prompt` | Update prompt template |
| **Health** |||
| GET | `/health` | Application health check |
| GET | `/api/scheduler/status` | Scheduler status and next run |

### Request/Response Examples

```python
# POST /api/sources
{
    "name": "Simon Willison's Weblog",
    "category": "newsletter",
    "source_type": "rss",
    "url": "https://simonwillison.net/atom/everything",
    "description": "LLM implementation, security, prompt engineering",
    "priority": 9,
    "is_active": true
}

# GET /api/briefings/latest
{
    "id": 42,
    "title": "Sunday Briefing Pack - Week 52, 2025",
    "week_start": "2025-12-23",
    "week_end": "2025-12-29",
    "executive_summary": "...",
    "full_content": "# Executive Brief\n\n1. **OpenAI...",
    "content_item_count": 147,
    "source_count": 34,
    "topics": ["enterprise-ai", "infrastructure", "regulation"],
    "notion_url": "https://notion.so/...",
    "created_at": "2025-12-29T06:00:00Z"
}
```

---

## 5. UI Wireframes

### Dashboard (index.html)

```
┌─────────────────────────────────────────────────────────────────┐
│  WEEKLY AI SIGINT                             [Settings] [Docs] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ NEXT SCHEDULED RUN  │  │   LAST BRIEFING     │              │
│  │ Sun, Dec 29 @ 6:00  │  │   Dec 22, 2025      │              │
│  │ [Run Now]           │  │   [View] [Notion]   │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ QUICK STATS                                                 ││
│  │ ─────────────────────────────────────────────────────────── ││
│  │ Active Sources: 87    │ Items This Week: 234  │ Briefings: 12││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ RECENT ACTIVITY                                             ││
│  │ ─────────────────────────────────────────────────────────── ││
│  │ • 2h ago: Fetched 12 items from SemiAnalysis               ││
│  │ • 2h ago: Fetched 8 items from Import AI                   ││
│  │ • 1d ago: Briefing exported to Notion                      ││
│  │ • 1d ago: Slack notification sent                          ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [Manage Sources]  [View Briefings]  [Edit Prompt]              │
└─────────────────────────────────────────────────────────────────┘
```

### Sources Editor (sources.html)

```
┌─────────────────────────────────────────────────────────────────┐
│  WATCHLIST SOURCES                                [+ Add Source]│
├─────────────────────────────────────────────────────────────────┤
│  Filter: [All Categories ▼] [Active Only ☑] [Search...]        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ NEWSLETTERS (12 sources)                              [─]   ││
│  │ ┌─────────────────────────────────────────────────────────┐ ││
│  │ │ ☑ The Batch (Andrew Ng)           RSS    Priority: 9   │ ││
│  │ │   https://deeplearning.ai/the-batch      [Edit] [Del]  │ ││
│  │ ├─────────────────────────────────────────────────────────┤ ││
│  │ │ ☑ Import AI (Jack Clark)          RSS    Priority: 9   │ ││
│  │ │   https://importai.substack.com          [Edit] [Del]  │ ││
│  │ └─────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ PEOPLE (30 sources)                                   [─]   ││
│  │ ...                                                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [Import JSON] [Export JSON]                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Settings (settings.html)

```
┌─────────────────────────────────────────────────────────────────┐
│  SETTINGS                                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  API CREDENTIALS                                                │
│  ─────────────────────────────────────────────────────────────  │
│  Anthropic API Key    [••••••••••••abcd]  [Update]  ✓ Valid    │
│  Notion Token         [••••••••••••1234]  [Update]  ✓ Valid    │
│  Slack Webhook URL    [https://hooks...]  [Update]  ✓ Valid    │
│                                                                 │
│  Note: Credentials stored locally with encryption.              │
│  Manual backup recommended.                                     │
│                                                                 │
│  SCHEDULE SETTINGS                                              │
│  ─────────────────────────────────────────────────────────────  │
│  Run Day:        [Sunday ▼]                                     │
│  Run Time:       [06:00 ]                                       │
│  Timezone:       [Europe/Madrid ▼]                              │
│                                                                 │
│  NOTION SETTINGS                                                │
│  ─────────────────────────────────────────────────────────────  │
│  Target Page ID: [abc123def456...]                              │
│                                                                 │
│  SYNTHESIS SETTINGS                                             │
│  ─────────────────────────────────────────────────────────────  │
│  Model:          [claude-sonnet-4-20250514 ▼]                   │
│  Max Tokens:     [16000]                                        │
│  Time Window:    [7] days                                       │
│                                                                 │
│  [Save Settings]                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Phase-Based Build Plan

### Overview

| Phase | Name | Scope | Files | Est. Time |
|-------|------|-------|-------|-----------|
| 1 | Foundation | Project setup, database, models | 8 new | 2-3 hours |
| 2 | Fetcher | RSS/web fetching, storage | 4 new, 2 modified | 2-3 hours |
| 3 | Synthesizer | Claude API integration | 3 new, 2 modified | 2-3 hours |
| 4 | Exports | Notion + Slack integration | 3 new, 2 modified | 2 hours |
| 5 | UI & Scheduling | Config UI, scheduler | 8 new, 3 modified | 3-4 hours |

---

### Phase 1: Foundation

#### Scope
- [x] Initialize project structure
- [x] Set up virtual environment and dependencies
- [x] Create SQLAlchemy models and database
- [x] Create FastAPI application skeleton
- [x] Implement configuration loading

#### DO NOT
- Implement fetching logic (Phase 2)
- Add Claude API integration (Phase 3)
- Build full UI (Phase 5)

#### Files to Create

**1. `requirements.txt`**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
aiosqlite==0.19.0
greenlet==3.0.3
python-dotenv==1.0.0
httpx==0.26.0
feedparser==6.0.10
beautifulsoup4==4.12.3
anthropic==0.18.0
notion-client==2.2.1
apscheduler==3.10.4
jinja2==3.1.3
cryptography==42.0.0
pydantic==2.5.3
pydantic-settings==2.1.0
```

**2. `.env.example`**
```bash
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Notion
NOTION_TOKEN=secret_...
NOTION_PAGE_ID=...

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# App Settings
DATABASE_URL=sqlite+aiosqlite:///./data/briefings.db
SECRET_KEY=your-secret-key-for-encryption
TIMEZONE=Europe/Madrid
```

**3. `app/config.py`**
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/briefings.db"
    secret_key: str = "change-me-in-production"
    timezone: str = "Europe/Madrid"
    anthropic_api_key: str = ""
    notion_token: str = ""
    notion_page_id: str = ""
    slack_webhook_url: str = ""
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

**4. `app/models/database.py`**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import get_settings

settings = get_settings()

# Create async engine with SQLite thread safety fix
engine = create_async_engine(
    settings.database_url, 
    echo=False,
    connect_args={"check_same_thread": False},  # Required for async SQLite
    pool_pre_ping=True,  # Verify connections before use
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    """Dependency for FastAPI routes - yields scoped session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

**5. `app/models/source.py`** — Full model as shown in Section 3

**6. `app/models/content.py`** — ContentItem model

**7. `app/models/briefing.py`** — Briefing model

**8. `app/main.py`**
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from app.models.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Weekly AI Sigint", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

#### Verification Gate 1

```bash
# 1. Verify project structure
ls -la app/
ls -la app/models/

# 2. Create virtual environment and install deps
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Create data directory
mkdir -p data

# 4. Copy env file
cp .env.example .env

# 5. Run application
uvicorn app.main:app --reload

# 6. Test health endpoint
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# 7. Verify database created
ls -la data/
# Expected: briefings.db exists
```

**GATE**: Do NOT proceed until health endpoint returns 200 and database file exists.

---

### Phase 2: Fetcher Service

#### Scope
- [x] Implement RSS feed fetcher
- [x] Implement basic web page fetcher
- [x] Add content deduplication
- [x] Create source CRUD endpoints
- [x] Store fetched content to database

#### DO NOT
- Add Claude synthesis (Phase 3)
- Implement scheduling (Phase 5)

#### Files to Create

**1. `app/services/fetcher.py`**
```python
import feedparser
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.source import Source
from app.models.content import ContentItem
import hashlib
import json

class FetcherService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def fetch_rss(self, source: Source) -> list[dict]:
        """Fetch items from RSS feed."""
        feed = feedparser.parse(source.url)
        items = []
        for entry in feed.entries:
            external_id = entry.get('id') or hashlib.sha256(
                entry.get('link', '').encode()
            ).hexdigest()[:32]
            
            items.append({
                'source_id': source.id,
                'external_id': external_id,
                'title': entry.get('title', 'Untitled'),
                'content': entry.get('summary', ''),
                'url': entry.get('link'),
                'author': entry.get('author'),
                'published_at': self._parse_date(entry.get('published')),
            })
        return items
    
    async def fetch_all_active(self, days_back: int = 7) -> int:
        """Fetch from all active sources. Returns count of new items."""
        stmt = select(Source).where(Source.is_active == True)
        result = await self.db.execute(stmt)
        sources = result.scalars().all()
        
        new_count = 0
        for source in sources:
            if source.source_type == 'rss':
                items = await self.fetch_rss(source)
                new_count += await self._store_items(items, days_back)
                source.last_fetched_at = datetime.utcnow()
        
        await self.db.commit()
        return new_count
    
    async def _store_items(self, items: list[dict], days_back: int) -> int:
        """Store items, skip duplicates, filter by date. Returns new count."""
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        new_count = 0
        
        for item in items:
            # Skip if too old
            if item.get('published_at') and item['published_at'] < cutoff:
                continue
            
            # Check for duplicate
            stmt = select(ContentItem).where(
                ContentItem.source_id == item['source_id'],
                ContentItem.external_id == item['external_id']
            )
            existing = await self.db.execute(stmt)
            if existing.scalar_one_or_none():
                continue
            
            # Store new item
            content_item = ContentItem(**item)
            self.db.add(content_item)
            new_count += 1
        
        return new_count
    
    def _parse_date(self, date_str: str) -> datetime | None:
        # Implementation for parsing various date formats
        pass
```

**2. `app/routers/sources.py`**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import get_db
from app.models.source import Source
from pydantic import BaseModel

router = APIRouter(prefix="/api/sources", tags=["sources"])

class SourceCreate(BaseModel):
    name: str
    category: str
    source_type: str
    url: str
    secondary_url: str | None = None
    description: str | None = None
    priority: int = 5
    is_active: bool = True

@router.get("")
async def list_sources(
    category: str | None = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Source)
    if category:
        stmt = stmt.where(Source.category == category)
    if active_only:
        stmt = stmt.where(Source.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("")
async def create_source(source: SourceCreate, db: AsyncSession = Depends(get_db)):
    db_source = Source(**source.model_dump())
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return db_source

# Additional CRUD endpoints...
```

**3. `app/routers/manual.py`**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.services.fetcher import FetcherService

router = APIRouter(prefix="/api/run", tags=["manual"])

@router.post("/fetch")
async def trigger_fetch(days_back: int = 7, db: AsyncSession = Depends(get_db)):
    fetcher = FetcherService(db)
    count = await fetcher.fetch_all_active(days_back)
    return {"status": "completed", "new_items": count}
```

#### Verification Gate 2

```bash
# 1. Verify files exist
ls -la app/services/fetcher.py
ls -la app/routers/sources.py
ls -la app/routers/manual.py

# 2. Start server
uvicorn app.main:app --reload

# 3. Add a test source
curl -X POST http://localhost:8000/api/sources \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Feed","category":"newsletter","source_type":"rss","url":"https://simonwillison.net/atom/everything"}'

# 4. Trigger fetch
curl -X POST http://localhost:8000/api/run/fetch

# 5. Verify content stored
curl http://localhost:8000/api/content
# Expected: Array with fetched items
```

**GATE**: Do NOT proceed until fetch returns items and they're stored in database.

---

### Phase 3: Synthesizer Service

#### Scope
- [x] Implement Claude API integration
- [x] Create prompt template system
- [x] Build content-to-briefing pipeline
- [x] Store briefing with metadata
- [x] Add briefing endpoints

#### DO NOT
- Add Notion export (Phase 4)
- Add Slack notification (Phase 4)

#### Files to Create

**1. `prompts/sunday_briefing.md`** — Your full prompt template from the watchlist

**2. `app/services/synthesizer.py`**
```python
import anthropic
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.content import ContentItem
from app.models.briefing import Briefing
from app.config import get_settings
from pathlib import Path

class SynthesizerService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
    
    async def synthesize_briefing(self, days_back: int = 7) -> Briefing:
        """Generate briefing from recent content."""
        # 1. Gather content
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        stmt = select(ContentItem).where(
            ContentItem.fetched_at >= cutoff
        ).order_by(ContentItem.published_at.desc())
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        
        # 2. Format content for Claude
        content_text = self._format_content_for_synthesis(items)
        
        # 3. Load prompt template
        prompt_template = self._load_prompt_template()
        
        # 4. Call Claude
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            messages=[
                {"role": "user", "content": f"{prompt_template}\n\n---\n\nCONTENT TO SYNTHESIZE:\n\n{content_text}"}
            ]
        )
        
        briefing_content = message.content[0].text
        
        # 5. Create briefing record
        week_end = datetime.utcnow().date()
        week_start = week_end - timedelta(days=days_back)
        
        briefing = Briefing(
            title=f"Sunday Briefing Pack - {week_start.strftime('%b %d')} to {week_end.strftime('%b %d, %Y')}",
            week_start=week_start,
            week_end=week_end,
            full_content=briefing_content,
            content_item_count=len(items),
            source_count=len(set(i.source_id for i in items)),
            metadata={"model": "claude-sonnet-4-20250514", "input_tokens": message.usage.input_tokens}
        )
        
        self.db.add(briefing)
        await self.db.commit()
        await self.db.refresh(briefing)
        
        return briefing
    
    def _format_content_for_synthesis(self, items: list[ContentItem]) -> str:
        """Format content items into text for Claude."""
        sections = []
        for item in items:
            section = f"### {item.title}\n"
            section += f"Source: {item.source.name if item.source else 'Unknown'}\n"
            section += f"Date: {item.published_at}\n"
            section += f"URL: {item.url}\n\n"
            section += f"{item.content[:2000]}...\n\n---\n"
            sections.append(section)
        return "\n".join(sections)
    
    def _load_prompt_template(self) -> str:
        prompt_path = Path("prompts/sunday_briefing.md")
        if prompt_path.exists():
            return prompt_path.read_text()
        return "Synthesize the following content into a briefing."
```

**3. `app/routers/briefings.py`** — CRUD for briefings

#### Verification Gate 3

```bash
# 1. Verify synthesizer exists
ls -la app/services/synthesizer.py

# 2. Verify prompt template exists
ls -la prompts/sunday_briefing.md

# 3. Ensure ANTHROPIC_API_KEY is set
echo $ANTHROPIC_API_KEY | head -c 10

# 4. Trigger synthesis (requires content from Phase 2)
curl -X POST http://localhost:8000/api/run/synthesize

# 5. Get latest briefing
curl http://localhost:8000/api/briefings/latest
# Expected: JSON with full_content populated
```

**GATE**: Do NOT proceed until synthesis returns a complete briefing with markdown content.

---

### Phase 4: Exports (Notion + Slack)

#### Scope
- [x] Implement Notion page export
- [x] Implement Slack webhook notification
- [x] Add export endpoints
- [x] Extract top 5 trending items for Slack

#### Files to Create

**1. `app/services/notion_export.py`**
```python
from notion_client import Client
from app.config import get_settings
from app.models.briefing import Briefing

class NotionExporter:
    def __init__(self):
        self.settings = get_settings()
        self.client = Client(auth=self.settings.notion_token)
    
    async def export_briefing(self, briefing: Briefing) -> str:
        """Export briefing to Notion page. Returns page URL."""
        # Create child page under configured parent
        page = self.client.pages.create(
            parent={"page_id": self.settings.notion_page_id},
            properties={
                "title": [{"text": {"content": briefing.title}}]
            },
            children=self._markdown_to_blocks(briefing.full_content)
        )
        return page["url"]
    
    def _markdown_to_blocks(self, markdown: str) -> list:
        """Convert markdown to Notion blocks."""
        # Implementation for parsing markdown to Notion block format
        pass
```

**2. `app/services/slack_notify.py`**
```python
import httpx
from app.config import get_settings
from app.models.briefing import Briefing

class SlackNotifier:
    def __init__(self):
        self.settings = get_settings()
    
    async def notify(self, briefing: Briefing, top_items: list[dict]) -> bool:
        """Send Slack notification with top 5 items."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📰 {briefing.title}"}
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Top 5 Trending Items This Week:*"}
            }
        ]
        
        for i, item in enumerate(top_items[:5], 1):
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"{i}. *{item['title']}*\n{item['summary']}\n<{item['url']}|Read more>"}
            })
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.settings.slack_webhook_url,
                json={"blocks": blocks}
            )
            return response.status_code == 200
```

#### Verification Gate 4

```bash
# 1. Verify export services exist
ls -la app/services/notion_export.py
ls -la app/services/slack_notify.py

# 2. Test Notion export (requires valid tokens)
curl -X POST http://localhost:8000/api/run/export/notion

# 3. Test Slack notification
curl -X POST http://localhost:8000/api/run/notify/slack

# 4. Verify Notion page created (check Notion)
# 5. Verify Slack message received (check Slack channel)
```

**GATE**: Do NOT proceed until both Notion export and Slack notification succeed.

---

### Phase 5: UI & Scheduling

#### Scope
- [x] Create HTML templates with Tailwind
- [x] Implement configuration UI
- [x] Set up APScheduler for weekly runs
- [x] Add credential encryption
- [x] Final integration testing

#### Files to Create

**1. `app/templates/base.html`**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Weekly AI Sigint{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <nav class="bg-white shadow">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <span class="text-xl font-bold">📡 Weekly AI Sigint</span>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/" class="text-gray-700 hover:text-gray-900">Dashboard</a>
                    <a href="/sources" class="text-gray-700 hover:text-gray-900">Sources</a>
                    <a href="/briefings" class="text-gray-700 hover:text-gray-900">Briefings</a>
                    <a href="/settings" class="text-gray-700 hover:text-gray-900">Settings</a>
                </div>
            </div>
        </div>
    </nav>
    <main class="max-w-7xl mx-auto py-6 px-4">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

**2. `app/templates/index.html`** — Dashboard as wireframed

**3. `app/templates/sources.html`** — Source editor

**4. `app/templates/settings.html`** — Settings page

**5. `app/templates/briefings.html`** — Briefing history

**6. `app/templates/prompt.html`** — Prompt editor

**7. `app/services/scheduler.py`**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import get_settings

scheduler = AsyncIOScheduler()

async def run_weekly_pipeline():
    """Execute full pipeline: fetch → synthesize → export → notify."""
    from app.services.fetcher import FetcherService
    from app.services.synthesizer import SynthesizerService
    from app.services.notion_export import NotionExporter
    from app.services.slack_notify import SlackNotifier
    from app.models.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        # 1. Fetch
        fetcher = FetcherService(db)
        await fetcher.fetch_all_active()
        
        # 2. Synthesize
        synthesizer = SynthesizerService(db)
        briefing = await synthesizer.synthesize_briefing()
        
        # 3. Export to Notion
        exporter = NotionExporter()
        notion_url = await exporter.export_briefing(briefing)
        briefing.notion_url = notion_url
        
        # 4. Notify Slack
        notifier = SlackNotifier()
        await notifier.notify(briefing, [])  # Top items extracted from briefing
        
        await db.commit()

def setup_scheduler():
    settings = get_settings()
    # Default: Sunday at 6:00 AM
    scheduler.add_job(
        run_weekly_pipeline,
        CronTrigger(day_of_week='sun', hour=6, minute=0, timezone=settings.timezone),
        id='weekly_briefing',
        replace_existing=True
    )
    scheduler.start()
```

**8. Update `app/main.py`** — Add template routes and scheduler startup

#### Verification Gate 5 (Final)

```bash
# 1. Verify all templates exist
ls -la app/templates/

# 2. Verify scheduler service
ls -la app/services/scheduler.py

# 3. Start application
uvicorn app.main:app --reload

# 4. Test UI pages
curl http://localhost:8000/          # Dashboard
curl http://localhost:8000/sources   # Sources page
curl http://localhost:8000/settings  # Settings page

# 5. Check scheduler status
curl http://localhost:8000/api/scheduler/status
# Expected: {"next_run": "2025-01-05T06:00:00", "status": "running"}

# 6. Run full pipeline manually
curl -X POST http://localhost:8000/api/run/full-pipeline

# 7. Verify:
# - New briefing in database
# - Page created in Notion
# - Message received in Slack
```

**GATE**: MVP complete when full pipeline runs successfully end-to-end.

---

## 7. CLAUDE.md Template

Save this as `CLAUDE.md` in the project root:

```markdown
# Weekly AI Sigint

> A locally-hosted app that fetches AI/enterprise tech content weekly, synthesizes briefings with Claude, exports to Notion, and notifies via Slack.

## Quick Start

```bash
# 1. Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# 2. Run
mkdir -p data
uvicorn app.main:app --reload

# 3. Access
open http://localhost:8000
```

## Project Structure

```
app/
├── main.py              # FastAPI entry point
├── config.py            # Settings from .env
├── models/              # SQLAlchemy models
├── services/            # Business logic (fetcher, synthesizer, exports)
├── routers/             # API endpoints
└── templates/           # Jinja2 HTML templates
data/
└── briefings.db         # SQLite database
prompts/
└── sunday_briefing.md   # Claude prompt template
```

## Development Workflow

1. **Add source**: POST /api/sources or use UI
2. **Test fetch**: POST /api/run/fetch
3. **Test synthesis**: POST /api/run/synthesize
4. **Test export**: POST /api/run/export/notion
5. **Run full pipeline**: POST /api/run/full-pipeline

## Environment Variables

See `.env.example` for all required variables.

## Common Commands

```bash
# Start dev server
uvicorn app.main:app --reload

# Run tests
pytest tests/

# Check scheduler
curl http://localhost:8000/api/scheduler/status

# Manual full pipeline
curl -X POST http://localhost:8000/api/run/full-pipeline
```

## Database

SQLite at `data/briefings.db`. Tables: sources, content_items, briefings, credentials, config.

## Troubleshooting

- **Port in use**: `lsof -i :8000` then `kill -9 <PID>`
- **Missing deps**: `pip install -r requirements.txt`
- **API key errors**: Check `.env` values, restart server
```

---

## 8. Known Pitfalls & Mitigations

### Pitfall 1: RSS Feed Parsing Variations
**Problem**: Different RSS feeds have inconsistent date formats, missing fields.
**Mitigation**: Implement robust date parsing with multiple format attempts. Use `.get()` with defaults for all fields.

### Pitfall 2: Rate Limiting
**Problem**: Fetching too many sources too quickly triggers rate limits.
**Mitigation**: Add delays between fetches (1-2 seconds). Implement exponential backoff on 429 responses.

### Pitfall 3: Claude Token Limits
**Problem**: Too much content exceeds Claude's context window.
**Mitigation**: Truncate individual items to 2000 chars. Implement content prioritization by source priority. Split into multiple calls if needed.

### Pitfall 4: Notion Block Limits
**Problem**: Notion API has limits on blocks per request (100) and content length.
**Mitigation**: Chunk large briefings into multiple append operations. Implement pagination for very long content.

### Pitfall 5: Async SQLAlchemy Session Management
**Problem**: Session lifecycle issues in async context.
**Mitigation**: Always use `async with` for sessions. Never share sessions across async tasks.

### Pitfall 6: Credential Encryption Key Loss
**Problem**: Changing SECRET_KEY makes stored credentials unreadable.
**Mitigation**: Document that SECRET_KEY must be backed up. Add credential export/import as plaintext (with warning).

### Pitfall 7: Scheduler Not Starting
**Problem**: Scheduler doesn't persist across restarts without explicit startup.
**Mitigation**: Call `setup_scheduler()` in FastAPI lifespan. Store schedule config in database, not just code.

### Pitfall 8: Timezone Confusion
**Problem**: Mixing UTC and local times causes scheduling issues.
**Mitigation**: Store all times as UTC in database. Convert to user timezone only for display. Use `pytz` explicitly.

### Pitfall 9: macOS GNU Coreutils Missing
**Problem**: Commands like `timeout` fail on macOS — they're GNU coreutils not available by default.
**Mitigation**: Use `gtimeout` (from `brew install coreutils`) or Python-based alternatives. Test on both Linux and macOS.

### Pitfall 10: Python Async Needs greenlet
**Problem**: SQLAlchemy async fails with `greenlet` import error on some systems.
**Mitigation**: Explicitly include `greenlet==3.0.3` in requirements.txt for any async SQLAlchemy project.

---

## 9. File Manifest

### Phase 1 (Foundation)
| File | Type | Purpose |
|------|------|---------|
| `requirements.txt` | Config | Python dependencies |
| `.env.example` | Config | Environment template |
| `.gitignore` | Config | Git ignore rules |
| `app/__init__.py` | Python | Package init |
| `app/main.py` | Python | FastAPI application |
| `app/config.py` | Python | Settings management |
| `app/models/__init__.py` | Python | Package init |
| `app/models/database.py` | Python | SQLAlchemy setup |
| `app/models/source.py` | Python | Source model |
| `app/models/content.py` | Python | ContentItem model |
| `app/models/briefing.py` | Python | Briefing model |

### Phase 2 (Fetcher)
| File | Type | Purpose |
|------|------|---------|
| `app/services/__init__.py` | Python | Package init |
| `app/services/fetcher.py` | Python | Content fetching |
| `app/routers/__init__.py` | Python | Package init |
| `app/routers/sources.py` | Python | Source CRUD API |
| `app/routers/content.py` | Python | Content API |
| `app/routers/manual.py` | Python | Manual triggers |

### Phase 3 (Synthesizer)
| File | Type | Purpose |
|------|------|---------|
| `prompts/sunday_briefing.md` | Markdown | Prompt template |
| `app/services/synthesizer.py` | Python | Claude integration |
| `app/routers/briefings.py` | Python | Briefing API |

### Phase 4 (Exports)
| File | Type | Purpose |
|------|------|---------|
| `app/services/notion_export.py` | Python | Notion integration |
| `app/services/slack_notify.py` | Python | Slack webhook |

### Phase 5 (UI & Scheduling)
| File | Type | Purpose |
|------|------|---------|
| `app/services/scheduler.py` | Python | APScheduler setup |
| `app/routers/settings.py` | Python | Settings API |
| `app/templates/base.html` | HTML | Base template |
| `app/templates/index.html` | HTML | Dashboard |
| `app/templates/sources.html` | HTML | Source editor |
| `app/templates/settings.html` | HTML | Settings page |
| `app/templates/briefings.html` | HTML | Briefing history |
| `app/templates/prompt.html` | HTML | Prompt editor |
| `app/static/css/custom.css` | CSS | Custom styles |

### Documentation
| File | Type | Purpose |
|------|------|---------|
| `CLAUDE.md` | Markdown | Claude Code instructions |
| `README.md` | Markdown | User documentation |

**Total: ~35 files**

---

## 10. Future Enhancements (Post-MVP)

### v1.1 — Analytics Dashboard
- Topic frequency trends over time
- Source reliability scoring
- Person/org mention tracking
- Interactive charts (Plotly/Chart.js)

### v1.2 — Enhanced Fetching
- Twitter/X API integration
- LinkedIn scraping (with auth)
- Podcast transcript fetching
- arXiv paper abstract parsing

### v1.3 — Multi-Format Export
- Email delivery (SMTP)
- PDF generation
- Obsidian markdown export
- Google Docs export

### v1.4 — Smart Prioritization
- ML-based relevance scoring
- Duplicate detection across sources
- Entity extraction and linking
- Custom topic classifiers

### v1.5 — Team Features
- Multi-user authentication
- Shared watchlists
- Collaborative annotations
- Role-based access

---

## Appendix: Import Script for Watchlist

Use this to bulk import your existing watchlist:

```python
# scripts/import_watchlist.py
import json
import asyncio
from app.models.database import AsyncSessionLocal
from app.models.source import Source

WATCHLIST = [
    # Newsletters
    {"name": "The Batch", "category": "newsletter", "source_type": "rss", 
     "url": "https://deeplearning.ai/the-batch", "priority": 9},
    {"name": "Import AI", "category": "newsletter", "source_type": "rss",
     "url": "https://importai.substack.com/feed", "priority": 9},
    # ... add all sources from your watchlist
]

async def import_sources():
    async with AsyncSessionLocal() as db:
        for source_data in WATCHLIST:
            source = Source(**source_data)
            db.add(source)
        await db.commit()
        print(f"Imported {len(WATCHLIST)} sources")

if __name__ == "__main__":
    asyncio.run(import_sources())
```

---

*End of Technical Proposal*
