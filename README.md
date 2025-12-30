# Weekly AI Sigint

> A locally-hosted app that fetches AI/enterprise tech content weekly, synthesizes briefings with Claude, and exports to Notion and Slack.

## Features

- 📡 **Content Aggregation**: Fetch from RSS feeds, Twitter, LinkedIn, blogs
- 🤖 **AI Synthesis**: Claude-powered weekly briefings
- 📝 **Notion Export**: Automatically publish to Notion
- 💬 **Slack Notifications**: Push briefings to Slack channels
- ⏰ **Automated Scheduling**: Weekly Sunday morning runs

## Quick Start

```bash
# 1. Setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Run
mkdir -p data
uvicorn app.main:app --reload

# 4. Access
open http://localhost:8000
```

## Configuration

Create a `.env` file with your credentials:

```bash
ANTHROPIC_API_KEY=<your-key>
NOTION_TOKEN=<your-token>
NOTION_PAGE_ID=<your-page-id>
SLACK_WEBHOOK_URL=<your-webhook-url>
```

See `.env.example` for all configuration options.

## Project Status

**Phase 1: Foundation** ✅ Complete
- Database models (sources, content, briefings)
- FastAPI application structure
- Configuration management

**Phase 2: Fetcher** 🚧 Next
- RSS feed parsing
- Content deduplication
- Watchlist management API

**Phase 3: Synthesizer** 📋 Planned
- Claude API integration
- Briefing generation
- Prompt templating

**Phase 4: Exports** 📋 Planned
- Notion integration
- Slack notifications

**Phase 5: UI + Scheduler** 📋 Planned
- Web interface
- Weekly automation
- Manual pipeline triggers

## Documentation

- [CLAUDE.md](weekly-ai-sigint-CLAUDE.md) - Development instructions for Claude Code
- [Proposal](weekly-ai-sigint-proposal.md) - Detailed project proposal
- [API Docs](http://localhost:8000/docs) - Interactive API documentation (when running)

## License

MIT
