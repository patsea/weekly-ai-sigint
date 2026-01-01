# Weekly AI Sigint — Phase 4 Verification

> Run these checks to verify Phase 4 implementation before proceeding to Phase 5.

## Instructions

Execute each section in order. Fix any issues found before proceeding to the next section.

---

## 1. Database Schema Verification

Check that the briefing model has all required export columns.

```bash
# Check current schema
sqlite3 data/briefings.db ".schema briefings"
```

**Required columns (verify these exist):**
- `notion_page_id` (TEXT/VARCHAR, nullable)
- `notion_url` (TEXT/VARCHAR, nullable)
- `notion_exported_at` (TIMESTAMP/DATETIME, nullable)
- `slack_notified_at` (TIMESTAMP/DATETIME, nullable)

**If any columns are missing**, add them:

```bash
# Add missing columns (run only if needed)
sqlite3 data/briefings.db "ALTER TABLE briefings ADD COLUMN notion_page_id TEXT;"
sqlite3 data/briefings.db "ALTER TABLE briefings ADD COLUMN notion_url TEXT;"
sqlite3 data/briefings.db "ALTER TABLE briefings ADD COLUMN notion_exported_at TIMESTAMP;"
sqlite3 data/briefings.db "ALTER TABLE briefings ADD COLUMN slack_notified_at TIMESTAMP;"

# Verify columns were added
sqlite3 data/briefings.db ".schema briefings"
```

Also verify the model file matches:

```bash
# Check model has the fields
grep -E "notion_page_id|notion_url|notion_exported_at|slack_notified_at" app/models/briefing.py
```

**If model is missing fields**, update `app/models/briefing.py` to include:

```python
notion_page_id = Column(String, nullable=True)
notion_url = Column(String, nullable=True)
notion_exported_at = Column(DateTime, nullable=True)
slack_notified_at = Column(DateTime, nullable=True)
```

---

## 2. Notion Export Service Verification

### 2.1 Check block chunking implementation

```bash
# Look for chunking logic (should handle 100-block Notion limit)
grep -n -E "chunk|100|batch|blocks\[" app/services/notion_export.py
```

**Expected**: Should see logic that splits blocks into chunks of ≤100.

### 2.2 Check return type matches Pydantic model

```bash
# Check what the service returns
grep -A 10 "async def export_briefing_to_notion" app/services/notion_export.py | head -15

# Check what the router expects
grep -A 5 "class NotionExportResult" app/routers/manual.py
```

**Expected**: Return dict keys should match model fields: `success`, `briefing_id`, `notion_page_id`, `notion_url`

### 2.3 Check text length handling

```bash
# Notion blocks have 2000 char limit - verify it's handled
grep -n "2000\|split\|truncate" app/services/notion_export.py
```

---

## 3. Slack Notify Service Verification

### 3.1 Check async httpx usage

```bash
# Should use async client, not sync
grep -n "httpx\|AsyncClient\|async with" app/services/slack_notify.py
```

**Expected**: Should see `httpx.AsyncClient()` with `async with` pattern, NOT `httpx.post()`.

### 3.2 Check return type matches Pydantic model

```bash
# Check what the service returns
grep -A 10 "async def send_briefing_to_slack" app/services/slack_notify.py | head -15

# Check what the router expects
grep -A 5 "class SlackNotifyResult" app/routers/manual.py
```

**Expected**: Return dict keys should match: `success`, `briefing_id`, `message`

### 3.3 Check Block Kit formatting

```bash
# Should use proper Slack Block Kit structure
grep -n "blocks\|type.*header\|type.*section\|mrkdwn" app/services/slack_notify.py | head -10
```

---

## 4. Configuration Validation

### 4.1 Check settings have the required fields

```bash
grep -E "NOTION_TOKEN|NOTION_PAGE_ID|SLACK_WEBHOOK_URL" app/config.py
```

**Expected**: All three should be defined in Settings class.

### 4.2 Check services validate config before use

```bash
# Notion export should check for valid token
grep -n "not.*NOTION\|raise.*ValueError\|not configured" app/services/notion_export.py | head -5

# Slack notify should check for valid webhook
grep -n "not.*SLACK\|raise.*ValueError\|not configured" app/services/slack_notify.py | head -5
```

**Expected**: Each service should raise ValueError if required config is missing/empty.

---

## 5. Runtime Verification

### 5.1 Start server and verify endpoints exist

```bash
# Kill any existing server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# Start server
source venv/bin/activate
uvicorn app.main:app --port 8000 > /tmp/phase4-test.log 2>&1 &
sleep 3

# Check server started
curl -s http://localhost:8000/health

# Verify all Phase 4 endpoints registered
curl -s http://localhost:8000/openapi.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
endpoints = ['/api/run/export/notion', '/api/run/notify/slack', '/api/run/full-pipeline']
for ep in endpoints:
    status = '✅' if ep in data['paths'] else '❌ MISSING'
    print(f'{status} {ep}')
"
```

### 5.2 Test error handling with no briefing

```bash
# Should return 400 with clear message, not 500 crash
curl -s -X POST http://localhost:8000/api/run/export/notion | python3 -m json.tool
curl -s -X POST http://localhost:8000/api/run/notify/slack | python3 -m json.tool
```

**Expected**: `{"detail": "No briefing found"}` or similar clear error.

### 5.3 Check server logs for errors

```bash
cat /tmp/phase4-test.log | grep -i "error\|exception\|traceback" | head -10
```

**Expected**: No errors during startup or endpoint calls.

### 5.4 Stop test server

```bash
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
```

---

## 6. Full Integration Test (When Credentials Available)

**Skip this section if using placeholder credentials. Run after adding real API keys.**

```bash
# Ensure real credentials in .env
grep -E "^ANTHROPIC_API_KEY=sk-ant|^NOTION_TOKEN=secret_|^SLACK_WEBHOOK_URL=https://hooks" .env

# Start fresh database
rm -f data/briefings.db

# Start server
source venv/bin/activate
uvicorn app.main:app --port 8000 > /tmp/integration-test.log 2>&1 &
sleep 3

# Add test source
curl -s -X POST http://localhost:8000/api/sources/ -H "Content-Type: application/json" -d '{"name":"Simon Willison","category":"person","source_type":"rss","url":"https://simonwillison.net/atom/everything","priority":9}'

# Fetch content
echo "=== FETCH ===" && curl -s -X POST http://localhost:8000/api/run/fetch | python3 -m json.tool | head -20

# Synthesize
echo "=== SYNTHESIZE ===" && curl -s -X POST "http://localhost:8000/api/run/synthesize?days_back=30" | python3 -m json.tool

# Export to Notion
echo "=== NOTION EXPORT ===" && curl -s -X POST http://localhost:8000/api/run/export/notion | python3 -m json.tool

# Slack notify
echo "=== SLACK NOTIFY ===" && curl -s -X POST http://localhost:8000/api/run/notify/slack | python3 -m json.tool

# Verify database state
echo "=== DATABASE STATE ===" && sqlite3 data/briefings.db "SELECT id, title, substr(notion_url, 1, 50) as notion_url, slack_notified_at FROM briefings ORDER BY id DESC LIMIT 1;"

# Check for any errors
echo "=== ERRORS ===" && cat /tmp/integration-test.log | grep -i "error\|exception" | head -10

# Cleanup
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
```

---

## 7. Summary Checklist

After running all checks, verify:

- [ ] Briefing model has all 4 export columns (notion_page_id, notion_url, notion_exported_at, slack_notified_at)
- [ ] Database schema matches model
- [ ] Notion export handles 100-block limit
- [ ] Notion export handles 2000-char text limit
- [ ] Slack notify uses async httpx (AsyncClient)
- [ ] Services validate config before use
- [ ] All 3 endpoints registered in OpenAPI
- [ ] Endpoints return proper errors (400) when no briefing exists
- [ ] No startup errors or tracebacks in logs

---

## 8. Issues Found

Document any issues found during verification:

```
Issue 1: [DESCRIPTION]
- File: 
- Fix needed:
- Status: [ ] Fixed

Issue 2: [DESCRIPTION]
- File:
- Fix needed:
- Status: [ ] Fixed
```

---

## 9. Next Steps

Once all checks pass:

1. Commit Phase 4:
   ```bash
   git add -A && git commit -m "Phase 4 complete: Notion and Slack exports verified"
   ```

2. Proceed to Phase 5: UI + Scheduler
