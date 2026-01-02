# Troubleshooting Guide

## Common Issues

### Server Won't Start

**Symptom:** `uvicorn app.main:app` fails immediately.

**Solutions:**

1. **Port in use:**
   ```bash
   lsof -ti :8000 | xargs kill -9
   ```

2. **Missing dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database error:**
   ```bash
   # Reinitialize database
   rm data/weekly_sigint.db
   python -c "from app.models.database import init_db; import asyncio; asyncio.run(init_db())"
   ```

4. **Import error:**
   ```bash
   # Check for syntax errors
   python -c "from app.main import app"
   ```

---

### Fetch Returns No Content

**Symptom:** `/api/run/fetch` returns 0 items.

**Solutions:**

1. **Check source URLs:**
   - Verify RSS feed URLs are valid
   - Test in browser or with `curl`

2. **Check source is active:**
   ```bash
   curl -s http://localhost:8000/api/sources/ | python3 -c "import sys,json; [print(str(s['name']) + ': active=' + str(s['active'])) for s in json.load(sys.stdin)]"
   ```

3. **Source has no recent content:**
   - Some sources update infrequently
   - Check `published_at` dates

---

### Synthesis Fails

**Symptom:** `/api/run/synthesize` returns error.

**Solutions:**

1. **Check API key:**
   ```bash
   grep ANTHROPIC_API_KEY .env
   # Should start with sk-ant-
   ```

2. **Test API key directly:**
   ```bash
   curl -s https://api.anthropic.com/v1/messages \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "content-type: application/json" \
     -H "anthropic-version: 2023-06-01" \
     -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
   ```

3. **No content to synthesize:**
   - Run fetch first
   - Check `days_back` parameter

4. **Rate limit hit:**
   - Wait and retry
   - Check Anthropic dashboard for usage

---

### Notion Export Fails

**Symptom:** Export returns error or nothing appears in Notion.

**Solutions:**

1. **Verify token:**
   ```bash
   grep NOTION_TOKEN .env
   # Should start with secret_
   ```

2. **Verify page ID:**
   - Page ID is the 32-character string from Notion URL
   - Example: `https://notion.so/My-Page-abc123def456...` → `abc123def456...`

3. **Check integration access:**
   - Go to Notion page → Share → Invite integration
   - Integration must have access to parent page

4. **Token permissions:**
   - Integration needs "Insert content" capability

---

### Slack Notification Fails

**Symptom:** No message in Slack channel.

**Solutions:**

1. **Verify webhook URL:**
   ```bash
   grep SLACK_WEBHOOK_URL .env
   # Should be https://hooks.slack.com/services/...
   ```

2. **Test webhook directly:**
   ```bash
   curl -X POST $SLACK_WEBHOOK_URL \
     -H "Content-Type: application/json" \
     -d '{"text":"Test from Weekly AI Sigint"}'
   ```

3. **Channel archived or deleted:**
   - Recreate webhook in Slack

4. **Webhook disabled:**
   - Check Slack app settings

---

### Scheduler Not Running

**Symptom:** Jobs don't execute at scheduled time.

**Solutions:**

1. **Check scheduler status:**
   ```bash
   curl -s http://localhost:8000/api/scheduler/status | python3 -m json.tool
   ```

2. **Scheduler paused:**
   ```bash
   curl -X POST http://localhost:8000/api/scheduler/resume
   ```

3. **Wrong timezone:**
   - Check `TIMEZONE` in `.env`
   - Use IANA timezone names (e.g., `Europe/London`)

4. **Server restarted:**
   - Scheduler starts fresh; past jobs not recovered

---

### Database Locked

**Symptom:** SQLite "database is locked" error.

**Solutions:**

1. **Multiple processes accessing DB:**
   ```bash
   lsof data/weekly_sigint.db
   # Kill extra processes
   ```

2. **Journal file stuck:**
   ```bash
   rm data/weekly_sigint.db-journal
   rm data/weekly_sigint.db-wal
   rm data/weekly_sigint.db-shm
   ```

3. **Restart server:**
   ```bash
   lsof -ti :8000 | xargs kill -9
   uvicorn app.main:app --port 8000
   ```

---

### High Memory Usage

**Symptom:** Server using excessive RAM.

**Solutions:**

1. **Large briefings in memory:**
   - Briefings are cached; restart clears cache

2. **Job history growing:**
   - History is limited to 10 entries; shouldn't be issue

3. **Memory leak:**
   - Restart server periodically
   - Check for unclosed database sessions

---

## Debug Mode

Enable detailed logging:

```python
# In app/main.py or startup
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or via environment:

```bash
export LOG_LEVEL=DEBUG
uvicorn app.main:app --port 8000
```

## Getting Help

1. Check server logs: `tail -f logs/server.log`
2. Check API response: `curl ... | python3 -m json.tool`
3. Verify configuration: `cat .env`
4. Test components individually before full pipeline
