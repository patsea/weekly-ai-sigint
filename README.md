# Weekly AI Sigint

<!-- AUTO-GENERATED: Recent Changes -->
### Recent Activity

**Last Updated**: 2026-01-18
**Commits This Week**: 3

**Recent Changes** (12 files):
- `.gitignore`
- `FIX_FETCHER_FULL_CONTENT.md`
- `README.md`
- `RESTORE_SUNDAY_BRIEFING_PROMPT.md`
- `SETUP_WEEKLY_AI_SIGINT_LAUNCHD.md`
- `app/models/briefing.py`
- `app/routers/briefings.py`
- `app/templates/briefings.html`
- `prompts/sunday_briefing.md`
- `prompts/sunday_briefing.md.backup`
- ... and 2 more
<!-- END AUTO-GENERATED -->


> AI-powered weekly intelligence briefing system for tracking AI and enterprise technology developments.

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

Weekly AI Sigint is a locally-hosted application that:

1. **Fetches** content from curated AI/tech sources (RSS feeds, newsletters, blogs)
2. **Synthesizes** a weekly briefing using Claude AI
3. **Exports** to Notion for archival and sharing
4. **Notifies** via Slack when new briefings are ready
5. **Schedules** automatic weekly runs

Perfect for executives, researchers, and technologists who want to stay informed about AI developments without manual curation.

## Features

- 🔄 **Automated Content Fetching** — RSS, newsletters, and web sources
- 🤖 **AI Synthesis** — Claude generates concise, actionable briefings
- 📝 **Notion Export** — Automatic archival with formatted pages
- 💬 **Slack Notifications** — Team alerts when briefings are ready
- 📅 **Weekly Scheduling** — Configurable cron-style automation
- 🖥️ **Web UI** — Manage sources, view briefings, configure settings
- 🔧 **Prompt Editor** — Customize the briefing generation prompt

## Quick Start

### Prerequisites

- Python 3.9+
- Anthropic API key (Claude)
- Optional: Notion API token + page ID
- Optional: Slack webhook URL

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/weekly-ai-sigint.git
cd weekly-ai-sigint

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or your preferred editor

# Initialize database
python -c "from app.models.database import init_db; import asyncio; asyncio.run(init_db())"

# Start server
uvicorn app.main:app --reload --port 8000
```

### Access the Application

Open http://localhost:8000 in your browser.

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-api03-...` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NOTION_TOKEN` | Notion integration token | — |
| `NOTION_PAGE_ID` | Parent page for briefings | — |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook | — |
| `WEEKLY_RUN_DAY` | Day for scheduled runs | `sun` |
| `WEEKLY_RUN_HOUR` | Hour (0-23) for scheduled runs | `6` |
| `WEEKLY_RUN_MINUTE` | Minute (0-59) for scheduled runs | `0` |
| `TIMEZONE` | Timezone for scheduling | `UTC` |
| `DATABASE_URL` | SQLite database path | `sqlite+aiosqlite:///data/weekly_sigint.db` |

## Usage

### Web Interface

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Overview, quick actions, scheduler status |
| Sources | `/sources` | Manage content sources |
| Briefings | `/briefings` | View past briefings |
| Settings | `/settings` | Configure API keys and schedule |
| Prompt | `/prompt` | Edit the synthesis prompt |

### Manual Operations

From the Dashboard, you can:

1. **Fetch Content** — Pull latest items from all active sources
2. **Synthesize Briefing** — Generate a new briefing from recent content
3. **Run Full Pipeline** — Fetch + Synthesize + Export + Notify
4. **Pause/Resume Scheduler** — Control automatic runs

### API Endpoints

See [API Documentation](docs/API.md) for full reference.

Key endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sources/` | List all sources |
| POST | `/api/run/fetch` | Fetch content from sources |
| POST | `/api/run/synthesize` | Generate new briefing |
| POST | `/api/run/export/notion` | Export to Notion |
| POST | `/api/run/notify/slack` | Send Slack notification |
| GET | `/api/scheduler/status` | Get scheduler status |
| POST | `/api/scheduler/run-now` | Trigger full pipeline |

## Adding Sources

### Via Web UI

1. Navigate to `/sources`
2. Click "Add Source"
3. Fill in source details:
   - **Name**: Display name
   - **Category**: newsletter, person, organization, media, research
   - **Type**: rss, blog, newsletter, twitter, linkedin, company
   - **URL**: RSS feed or website URL
   - **Priority**: 1-10 (higher = more important)
   - **Active**: Enable/disable fetching

### Via API

```bash
curl -X POST http://localhost:8000/api/sources/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Import AI Newsletter",
    "category": "newsletter",
    "source_type": "rss",
    "url": "https://importai.substack.com/feed",
    "priority": 9,
    "active": true
  }'
```

## Architecture

```
weekly-ai-sigint/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models/              # SQLAlchemy models
│   │   ├── database.py      # Database connection
│   │   ├── source.py        # Source model
│   │   ├── content.py       # Content item model
│   │   └── briefing.py      # Briefing model
│   ├── routers/             # API routes
│   │   ├── sources.py       # Source CRUD
│   │   ├── content.py       # Content endpoints
│   │   ├── briefings.py     # Briefing endpoints
│   │   ├── manual.py        # Manual trigger endpoints
│   │   ├── settings.py      # Settings endpoints
│   │   ├── prompt.py        # Prompt editor endpoints
│   │   ├── scheduler.py     # Scheduler control
│   │   └── views.py         # HTML page routes
│   ├── services/            # Business logic
│   │   ├── fetcher.py       # Content fetching
│   │   ├── synthesizer.py   # Claude synthesis
│   │   ├── notion_export.py # Notion integration
│   │   ├── slack_notify.py  # Slack integration
│   │   └── scheduler.py     # APScheduler service
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS and static assets
├── prompts/
│   └── sunday_briefing.md   # Synthesis prompt template
├── data/
│   └── weekly_sigint.db     # SQLite database
├── tests/                   # Unit tests
├── docs/                    # Documentation
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment template
└── requirements.txt         # Python dependencies
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

### Code Style

```bash
# Format code
black app/ tests/

# Type checking
mypy app/
```

## Deployment

See [Deployment Guide](docs/DEPLOYMENT.md) for production setup.

### Quick Deploy (Local)

```bash
# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# With auto-restart on crash
while true; do uvicorn app.main:app --port 8000; sleep 5; done
```

### Keep Running (macOS/Linux)

```bash
# Using nohup
nohup uvicorn app.main:app --port 8000 > logs/server.log 2>&1 &

# Using screen
screen -S sigint
uvicorn app.main:app --port 8000
# Ctrl+A, D to detach
```

## Troubleshooting

See [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for common issues.

### Quick Fixes

| Issue | Solution |
|-------|----------|
| Port in use | `lsof -ti :8000 \| xargs kill -9` |
| Database locked | Stop server, delete `.db-journal` files |
| Scheduler not running | Check logs for startup errors |
| Notion export fails | Verify token has page access |

## License

MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Anthropic Claude](https://anthropic.com) — AI synthesis
- [FastAPI](https://fastapi.tiangolo.com) — Web framework
- [APScheduler](https://apscheduler.readthedocs.io) — Job scheduling
- [Notion API](https://developers.notion.com) — Export integration
- [Slack API](https://api.slack.com) — Notifications
