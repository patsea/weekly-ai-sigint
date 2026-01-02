# Deployment Guide

## Local Development

### Requirements

- Python 3.9+
- 512MB RAM minimum
- 1GB disk space (for database growth)

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start development server
uvicorn app.main:app --reload --port 8000
```

## Production Deployment

### Option 1: Direct Python (Recommended for Local)

```bash
# Start server
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Keep running with nohup
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &
echo $! > .pid

# Stop server
kill $(cat .pid)
```

### Option 2: systemd Service (Linux)

Create `/etc/systemd/system/weekly-sigint.service`:

```ini
[Unit]
Description=Weekly AI Sigint
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/weekly-ai-sigint
Environment="PATH=/path/to/weekly-ai-sigint/venv/bin"
ExecStart=/path/to/weekly-ai-sigint/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable weekly-sigint
sudo systemctl start weekly-sigint

# Check status
sudo systemctl status weekly-sigint

# View logs
sudo journalctl -u weekly-sigint -f
```

### Option 3: launchd (macOS)

Create `~/Library/LaunchAgents/com.weekly-sigint.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.weekly-sigint</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/weekly-ai-sigint/venv/bin/uvicorn</string>
        <string>app.main:app</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/weekly-ai-sigint</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/weekly-ai-sigint/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/weekly-ai-sigint/logs/stderr.log</string>
</dict>
</plist>
```

```bash
# Load service
launchctl load ~/Library/LaunchAgents/com.weekly-sigint.plist

# Unload service
launchctl unload ~/Library/LaunchAgents/com.weekly-sigint.plist
```

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...

# Notion (optional)
NOTION_TOKEN=secret_...
NOTION_PAGE_ID=abc123...

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Scheduler
WEEKLY_RUN_DAY=sun      # mon, tue, wed, thu, fri, sat, sun
WEEKLY_RUN_HOUR=6       # 0-23
WEEKLY_RUN_MINUTE=0     # 0-59
TIMEZONE=Europe/Madrid  # Or UTC, America/New_York, etc.

# Database
DATABASE_URL=sqlite+aiosqlite:///data/weekly_sigint.db
```

### Timezone Configuration

Use standard IANA timezone names:

| Region | Timezone |
|--------|----------|
| UTC | `UTC` |
| London | `Europe/London` |
| Madrid | `Europe/Madrid` |
| New York | `America/New_York` |
| Los Angeles | `America/Los_Angeles` |
| Tokyo | `Asia/Tokyo` |

## Backup

### Database Backup

```bash
# Backup SQLite database
cp data/weekly_sigint.db backups/weekly_sigint_$(date +%Y%m%d).db

# Automated daily backup (cron)
0 2 * * * cp /path/to/data/weekly_sigint.db /path/to/backups/weekly_sigint_$(date +\%Y\%m\%d).db
```

### Configuration Backup

```bash
# Backup .env (contains secrets!)
cp .env backups/.env.$(date +%Y%m%d)

# Backup prompts
cp -r prompts/ backups/prompts_$(date +%Y%m%d)/
```

## Security Considerations

### Local Network Only

By default, bind to `0.0.0.0` only if you trust your network. For public access, add authentication.

### API Key Protection

- Never commit `.env` to git
- Use file permissions: `chmod 600 .env`
- Rotate keys periodically

### Database Security

- SQLite database contains all content and briefings
- Backup regularly
- Consider encryption for sensitive deployments

## Monitoring

### Health Check

```bash
# Check if server is running
curl -s http://localhost:8000/health | python3 -m json.tool

# Check scheduler status
curl -s http://localhost:8000/api/scheduler/status | python3 -m json.tool
```

### Log Files

```bash
# View recent logs
tail -f logs/server.log

# Search for errors
grep -i error logs/server.log | tail -20
```

### Disk Usage

```bash
# Check database size
du -h data/weekly_sigint.db

# Check log size
du -h logs/
```

## Updating

```bash
# Stop server
lsof -ti :8000 | xargs kill -9

# Pull updates
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Run migrations (if any)
# python -m alembic upgrade head

# Start server
uvicorn app.main:app --port 8000
```
