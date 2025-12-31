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
weekly-ai-sigint/
├── CLAUDE.md              # This file - Claude Code instructions
├── README.md              # User documentation
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── .env                   # Local environment (gitignored)
│
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Settings from .env
│   │
│   ├── models/            # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── database.py    # DB setup and session
│   │   ├── source.py      # Watchlist source model
│   │   ├── content.py     # Fetched content model
│   │   └── briefing.py    # Synthesized briefing model
│   │
│   ├── services/          # Business logic
│   │   ├── __init__.py
│   │   ├── fetcher.py     # RSS/web content fetching
│   │   ├── synthesizer.py # Claude API integration
│   │   ├── notion_export.py
│   │   ├── slack_notify.py
│   │   └── scheduler.py   # APScheduler weekly trigger
│   │
│   ├── routers/           # API endpoints
│   │   ├── __init__.py
│   │   ├── sources.py     # Watchlist CRUD
│   │   ├── content.py     # Fetched content queries
│   │   ├── briefings.py   # Briefing CRUD
│   │   ├── settings.py    # Config/credentials
│   │   └── manual.py      # Manual pipeline triggers
│   │
│   ├── templates/         # Jinja2 HTML (Tailwind)
│   │   ├── base.html
│   │   ├── index.html     # Dashboard
│   │   ├── sources.html   # Watchlist editor
│   │   ├── settings.html  # Credentials manager
│   │   ├── briefings.html # History viewer
│   │   └── prompt.html    # Prompt template editor
│   │
│   └── static/
│       └── css/
│           └── custom.css
│
├── data/
│   └── briefings.db       # SQLite database (gitignored)
│
├── prompts/
│   └── sunday_briefing.md # Claude prompt template
│
└── tests/
    ├── __init__.py
    ├── test_fetcher.py
    ├── test_synthesizer.py
    └── test_exports.py
```

## Development Workflow

### Adding a Source
```bash
# Via API
curl -X POST http://localhost:8000/api/sources \
  -H "Content-Type: application/json" \
  -d '{"name":"Import AI","category":"newsletter","source_type":"rss","url":"https://importai.substack.com/feed","priority":9}'

# Or use the web UI at /sources
```

### Testing the Pipeline
```bash
# 1. Fetch content from all active sources
curl -X POST http://localhost:8000/api/run/fetch

# 2. Synthesize briefing with Claude
curl -X POST http://localhost:8000/api/run/synthesize

# 3. Export to Notion
curl -X POST http://localhost:8000/api/run/export/notion

# 4. Send Slack notification
curl -X POST http://localhost:8000/api/run/notify/slack

# Or run the full pipeline at once
curl -X POST http://localhost:8000/api/run/full-pipeline
```

### Checking Status
```bash
# Health check
curl http://localhost:8000/health

# Scheduler status (next run time)
curl http://localhost:8000/api/scheduler/status

# Latest briefing
curl http://localhost:8000/api/briefings/latest
```

## Environment Variables

```bash
# .env.example
ANTHROPIC_API_KEY=sk-ant-...
NOTION_TOKEN=secret_...
NOTION_PAGE_ID=...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
DATABASE_URL=sqlite+aiosqlite:///./data/briefings.db
SECRET_KEY=your-secret-key-for-credential-encryption
TIMEZONE=Europe/Madrid
```

## Common Commands

```bash
# Start development server
uvicorn app.main:app --reload

# Start with specific port
uvicorn app.main:app --reload --port 8080

# Run tests
pytest tests/ -v

# Type checking (if using mypy)
mypy app/

# Check what's using a port
lsof -i :8000

# Kill process on port
kill -9 $(lsof -t -i :8000)
```

## Database

SQLite database at `data/briefings.db`

### Tables
- `sources` — Watchlist items (RSS feeds, people, orgs)
- `content_items` — Raw fetched content with deduplication
- `briefings` — Synthesized weekly briefings
- `briefing_sources` — Junction table for traceability
- `credentials` — Encrypted API keys
- `config` — Application settings

### Useful Queries
```bash
# Connect to SQLite
sqlite3 data/briefings.db

# Count sources by category
SELECT category, COUNT(*) FROM sources GROUP BY category;

# Recent content items
SELECT title, published_at FROM content_items ORDER BY published_at DESC LIMIT 10;

# Briefing history
SELECT id, title, created_at FROM briefings ORDER BY created_at DESC;
```

## Build Phases

This project was built in 5 phases. If resuming or debugging:

| Phase | Focus | Key Files |
|-------|-------|-----------|
| 1 | Foundation | models/, config.py, main.py |
| 2 | Fetcher | services/fetcher.py, routers/sources.py |
| 3 | Synthesizer | services/synthesizer.py, prompts/ |
| 4 | Exports | services/notion_export.py, slack_notify.py |
| 5 | UI + Scheduler | templates/, services/scheduler.py |

## Verification Commands

Use these to verify each component works:

```bash
# Phase 1: Foundation
curl http://localhost:8000/health
ls -la data/briefings.db

# Phase 2: Fetcher
curl http://localhost:8000/api/sources
curl -X POST http://localhost:8000/api/run/fetch

# Phase 3: Synthesizer
curl -X POST http://localhost:8000/api/run/synthesize
curl http://localhost:8000/api/briefings/latest

# Phase 4: Exports
curl -X POST http://localhost:8000/api/run/export/notion
curl -X POST http://localhost:8000/api/run/notify/slack

# Phase 5: Full system
curl http://localhost:8000/api/scheduler/status
curl -X POST http://localhost:8000/api/run/full-pipeline
```

## Troubleshooting

### Port Already in Use
```bash
lsof -i :8000
kill -9 <PID>
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### API Key Errors
1. Check `.env` file exists and has correct values
2. Restart the server after changing `.env`
3. Verify key format (Anthropic: `sk-ant-...`, Notion: `secret_...`)

### Database Issues
```bash
# Reset database (WARNING: deletes all data)
rm data/briefings.db
# Restart server - will recreate tables
```

### Scheduler Not Running
```bash
# Check status
curl http://localhost:8000/api/scheduler/status

# If not running, restart server
# Scheduler initializes on startup
```

### Claude API Errors
- Check token limits (default 16000 max_tokens)
- Verify content isn't exceeding context window
- Check Anthropic API status: https://status.anthropic.com

### macOS-Specific Issues

**`timeout: command not found`**
```bash
# timeout is GNU coreutils, not available on macOS by default
# Option 1: Install GNU coreutils
brew install coreutils
gtimeout 5 command  # Use gtimeout instead

# Option 2: Use Python-based alternative
python -c "import subprocess; subprocess.run(['command'], timeout=5)"
```

**`greenlet` import error with async SQLAlchemy**
```bash
# Ensure greenlet is installed
pip install greenlet==3.0.3
```

**Background process loses venv**
```bash
# Use explicit path instead of relying on activation
./venv/bin/uvicorn app.main:app &

# Or keep activation in subshell
(source venv/bin/activate && uvicorn app.main:app) &
```

### SQLite Async Thread Errors

**`SQLite objects created in a thread can only be used in that same thread`**

This occurs when SQLite connections are reused across async contexts. Fix by updating `app/models/database.py`:

```python
# Ensure these settings are present:
engine = create_async_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Critical fix
    pool_pre_ping=True,
)

# Use async_sessionmaker (not sessionmaker)
from sqlalchemy.ext.asyncio import async_sessionmaker
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

If error persists after fix, restart the server to pick up changes.

## Key Design Decisions

1. **SQLite over Postgres** — Local-only, single user, no external DB dependency
2. **APScheduler over Celery** — Simpler for weekly cron, no Redis needed
3. **Jinja2 over React** — Minimal UI, server-rendered, faster to build
4. **feedparser for RSS** — Battle-tested, handles format variations
5. **Fernet encryption for credentials** — Simple symmetric encryption, good enough for local storage

## Contributing / Extending

### Adding a New Source Type
1. Add handler in `services/fetcher.py`
2. Update `source_type` enum in `models/source.py`
3. Add UI option in `templates/sources.html`

### Adding a New Export Target
1. Create `services/new_export.py`
2. Add endpoint in `routers/manual.py`
3. Add credentials field in settings UI

### Modifying the Prompt
Edit `prompts/sunday_briefing.md` or use the web UI at `/prompt`
