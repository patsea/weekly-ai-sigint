# Weekly AI Sigint — Full End-to-End Test

> Complete verification of the entire MVP pipeline after Phase 5F completion.

## Prerequisites

Before running E2E tests, ensure you have:

- [ ] Valid `ANTHROPIC_API_KEY` in `.env`
- [ ] Valid `NOTION_TOKEN` and `NOTION_PAGE_ID` in `.env` (optional but recommended)
- [ ] Valid `SLACK_WEBHOOK_URL` in `.env` (optional but recommended)
- [ ] At least 2 active sources configured
- [ ] Python venv activated

---

## Pre-Flight Checklist

```bash
# 1. Verify working directory
pwd  # Should be weekly-ai-sigint

# 2. Activate venv
source venv/bin/activate

# 3. Kill any existing server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# 4. Verify .env has required keys
grep -E "^ANTHROPIC_API_KEY=|^NOTION_TOKEN=|^SLACK_WEBHOOK_URL=" .env | wc -l
# Expected: 1-3 (at minimum ANTHROPIC_API_KEY)

# 5. Check database exists
ls -la data/weekly_sigint.db

# 6. Start server
uvicorn app.main:app --port 8000 > /tmp/e2e-test.log 2>&1 &
sleep 3

# 7. Verify health
curl -s http://localhost:8000/health | python3 -m json.tool
```

---

## Stage 1: Infrastructure Verification

### 1.1 All Pages Load

```bash
echo "=== Stage 1.1: Page Load Tests ==="

# Dashboard
curl -s -o /dev/null -w "Dashboard: %{http_code}\n" http://localhost:8000/

# Sources
curl -s -o /dev/null -w "Sources: %{http_code}\n" http://localhost:8000/sources

# Briefings
curl -s -o /dev/null -w "Briefings: %{http_code}\n" http://localhost:8000/briefings

# Settings
curl -s -o /dev/null -w "Settings: %{http_code}\n" http://localhost:8000/settings

# Prompt
curl -s -o /dev/null -w "Prompt: %{http_code}\n" http://localhost:8000/prompt

# All should return 200
```

### 1.2 All API Endpoints Respond

```bash
echo "=== Stage 1.2: API Endpoint Tests ==="

# Sources API
curl -s http://localhost:8000/api/sources/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Sources API: OK ({len(d)} sources)')"

# Briefings API
curl -s http://localhost:8000/api/briefings/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Briefings API: OK ({len(d)} briefings)')"

# Settings API
curl -s http://localhost:8000/api/settings/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Settings API: OK (Anthropic key set: {d[\"anthropic_api_key\"] != \"\"})')"

# Prompt API
curl -s http://localhost:8000/api/prompt/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Prompt API: OK ({d[\"word_count\"]} words)')"

# Scheduler API
curl -s http://localhost:8000/api/scheduler/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Scheduler API: OK (running: {d[\"running\"]})')"
```

### 1.3 Scheduler is Running

```bash
echo "=== Stage 1.3: Scheduler Status ==="

curl -s http://localhost:8000/api/scheduler/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Running: {d[\"running\"]}')
print(f'Paused: {d[\"paused\"]}')
print(f'Next run: {d[\"next_run\"]}')
print(f'Job count: {d[\"job_count\"]}')
"
```

---

## Stage 2: Source Management

### 2.1 Verify Existing Sources

```bash
echo "=== Stage 2.1: List Sources ==="

curl -s http://localhost:8000/api/sources/ | python3 -c "
import sys, json
sources = json.load(sys.stdin)
print(f'Total sources: {len(sources)}')
for s in sources:
    status = '✅' if s['active'] else '❌'
    print(f'  {status} {s[\"name\"]} ({s[\"category\"]}) - {s[\"url\"][:50]}...')
"
```

### 2.2 Create Test Source

```bash
echo "=== Stage 2.2: Create Test Source ==="

curl -s -X POST http://localhost:8000/api/sources/ -H "Content-Type: application/json" -d '{"name":"E2E Test Source","category":"newsletter","source_type":"rss","url":"https://e2e-test.example.com/feed","priority":5,"active":false}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Created source ID: {d[\"id\"]}')"
```

### 2.3 Delete Test Source

```bash
echo "=== Stage 2.3: Cleanup Test Source ==="

# Get the test source ID
TEST_SRC_ID=$(curl -s http://localhost:8000/api/sources/ | python3 -c "import sys,json; sources=json.load(sys.stdin); matches=[s['id'] for s in sources if 'E2E Test' in s.get('name','')]; print(matches[0] if matches else '')")

if [ -n "$TEST_SRC_ID" ]; then
    curl -s -X DELETE http://localhost:8000/api/sources/$TEST_SRC_ID -w "Deleted: %{http_code}\n"
else
    echo "No test source to delete"
fi
```

---

## Stage 3: Content Fetching

### 3.1 Fetch from All Sources

```bash
echo "=== Stage 3.1: Fetch Content ==="

# This may take 30-60 seconds depending on sources
curl -s -X POST "http://localhost:8000/api/run/fetch" | python3 -m json.tool

# Check content count
curl -s http://localhost:8000/api/content/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Total content items: {len(d)}')"
```

### 3.2 Verify Recent Content

```bash
echo "=== Stage 3.2: Recent Content ==="

curl -s "http://localhost:8000/api/content/?limit=5" | python3 -c "
import sys, json
items = json.load(sys.stdin)
print(f'Recent items (last 5):')
for item in items[:5]:
    print(f'  - {item[\"title\"][:60]}...')
    print(f'    Source: {item.get(\"source_id\", \"?\")} | Date: {item.get(\"published_at\", \"?\")}')
"
```

---

## Stage 4: Briefing Synthesis (Requires API Key)

### 4.1 Synthesize Briefing

```bash
echo "=== Stage 4.1: Synthesize Briefing ==="
echo "This may take 30-90 seconds..."

# Synthesize from last 7 days of content
curl -s -X POST "http://localhost:8000/api/run/synthesize?days_back=7" | python3 -m json.tool
```

### 4.2 Verify Briefing Created

```bash
echo "=== Stage 4.2: Verify Briefing ==="

curl -s http://localhost:8000/api/briefings/latest | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'detail' in d:
    print(f'ERROR: {d[\"detail\"]}')
else:
    print(f'Briefing ID: {d[\"id\"]}')
    print(f'Title: {d[\"title\"]}')
    print(f'Created: {d[\"created_at\"]}')
    print(f'Content length: {len(d.get(\"content\", \"\"))} chars')
    print(f'Notion exported: {d.get(\"notion_url\") is not None}')
    print(f'Slack notified: {d.get(\"slack_notified_at\") is not None}')
"
```

### 4.3 View Briefing Content (First 500 chars)

```bash
echo "=== Stage 4.3: Briefing Preview ==="

curl -s http://localhost:8000/api/briefings/latest | python3 -c "
import sys, json
d = json.load(sys.stdin)
content = d.get('content', 'No content')[:500]
print(content)
print('...[truncated]')
"
```

---

## Stage 5: Export to Notion (Requires Notion Token)

### 5.1 Export Latest Briefing

```bash
echo "=== Stage 5.1: Export to Notion ==="

curl -s -X POST http://localhost:8000/api/run/export/notion | python3 -m json.tool
```

### 5.2 Verify Export

```bash
echo "=== Stage 5.2: Verify Notion Export ==="

curl -s http://localhost:8000/api/briefings/latest | python3 -c "
import sys, json
d = json.load(sys.stdin)
url = d.get('notion_url')
exported_at = d.get('notion_exported_at')
if url:
    print(f'✅ Exported to Notion')
    print(f'   URL: {url}')
    print(f'   Time: {exported_at}')
else:
    print('❌ Not exported to Notion')
"
```

---

## Stage 6: Slack Notification (Requires Webhook)

### 6.1 Send Notification

```bash
echo "=== Stage 6.1: Send Slack Notification ==="

curl -s -X POST http://localhost:8000/api/run/notify/slack | python3 -m json.tool
```

### 6.2 Verify Notification

```bash
echo "=== Stage 6.2: Verify Slack Notification ==="

curl -s http://localhost:8000/api/briefings/latest | python3 -c "
import sys, json
d = json.load(sys.stdin)
notified_at = d.get('slack_notified_at')
if notified_at:
    print(f'✅ Slack notification sent: {notified_at}')
else:
    print('❌ Slack notification not sent')
"
```

---

## Stage 7: Scheduler Controls

### 7.1 Pause Scheduler

```bash
echo "=== Stage 7.1: Pause Scheduler ==="

curl -s -X POST http://localhost:8000/api/scheduler/pause | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Paused: {d[\"success\"]}')"

# Verify paused
curl -s http://localhost:8000/api/scheduler/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status - Paused: {d[\"paused\"]}')"
```

### 7.2 Resume Scheduler

```bash
echo "=== Stage 7.2: Resume Scheduler ==="

curl -s -X POST http://localhost:8000/api/scheduler/resume | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Resumed: {d[\"success\"]}')"

# Verify running
curl -s http://localhost:8000/api/scheduler/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status - Running: {d[\"running\"]}, Paused: {d[\"paused\"]}')"
```

### 7.3 Check Job History

```bash
echo "=== Stage 7.3: Job History ==="

curl -s http://localhost:8000/api/scheduler/history | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'History count: {d[\"count\"]}')
for run in d.get('history', [])[:3]:
    print(f'  - {run.get(\"started_at\", \"?\")}: success={run.get(\"success\", \"?\")}')
"
```

---

## Stage 8: Full Pipeline Test (Optional)

This runs the complete automated pipeline that the scheduler would execute:

```bash
echo "=== Stage 8: Full Pipeline (Manual Trigger) ==="
echo "This runs: Fetch → Synthesize → Notion → Slack"
echo "May take 2-3 minutes..."

curl -s -X POST http://localhost:8000/api/scheduler/run-now | python3 -m json.tool
```

---

## Stage 9: Error Log Check

```bash
echo "=== Stage 9: Error Log Check ==="

# Check for any errors during tests
ERROR_COUNT=$(cat /tmp/e2e-test.log | grep -ci "error\|exception\|traceback")
echo "Errors found: $ERROR_COUNT"

if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "Recent errors:"
    cat /tmp/e2e-test.log | grep -i "error\|exception\|traceback" | tail -10
fi
```

---

## Stage 10: Cleanup

```bash
echo "=== Stage 10: Cleanup ==="

# Stop server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
echo "✅ Server stopped"
```

---

## Quick All-in-One E2E Script

Run this single command to execute a condensed E2E test:

```bash
echo "=== Weekly AI Sigint E2E Test ===" && source venv/bin/activate && lsof -ti :8000 | xargs kill -9 2>/dev/null; uvicorn app.main:app --port 8000 > /tmp/e2e.log 2>&1 & sleep 3 && echo "1. Health:" && curl -s http://localhost:8000/health | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])" && echo "2. Pages:" && for p in "" sources briefings settings prompt; do curl -s -o /dev/null -w "$p:%{http_code} " http://localhost:8000/$p; done && echo "" && echo "3. Sources:" && curl -s http://localhost:8000/api/sources/ | python3 -c "import sys,json;print(f'{len(json.load(sys.stdin))} sources')" && echo "4. Scheduler:" && curl -s http://localhost:8000/api/scheduler/status | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'running={d[\"running\"]}, next={d[\"next_run\"]}')" && echo "5. Errors:" && cat /tmp/e2e.log | grep -ci "error" | xargs -I {} bash -c '[ {} -eq 0 ] && echo "✅ No errors" || echo "⚠️ {} errors"' && lsof -ti :8000 | xargs kill -9 && echo "=== E2E Complete ==="
```

---

## E2E Test Summary Checklist

After running all stages, verify:

### Infrastructure
- [ ] All 5 pages load (200 status)
- [ ] All API endpoints respond
- [ ] Scheduler is running
- [ ] No startup errors

### Data Flow
- [ ] Sources can be listed/created/deleted
- [ ] Content can be fetched from sources
- [ ] Briefing can be synthesized
- [ ] Briefing appears in list and latest

### Exports (if configured)
- [ ] Notion export succeeds (page URL returned)
- [ ] Slack notification succeeds (timestamp recorded)

### Scheduler
- [ ] Can pause/resume
- [ ] Status shows next run time
- [ ] Run-now triggers pipeline

### Logs
- [ ] No unhandled errors in log file

---

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| Fetch returns 0 items | Sources have no recent content | Check source URLs manually |
| Synthesize fails | Invalid API key or no content | Verify ANTHROPIC_API_KEY |
| Notion export fails | Invalid token or page ID | Verify NOTION_TOKEN and NOTION_PAGE_ID |
| Slack fails | Invalid webhook URL | Verify SLACK_WEBHOOK_URL format |
| Scheduler not running | Lifespan not triggering | Check app/main.py lifespan function |
| 500 errors | Code bug | Check /tmp/e2e-test.log for traceback |
