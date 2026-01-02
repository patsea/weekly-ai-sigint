# Weekly AI Sigint — Full End-to-End Test (v2)

**Created**: 2026-01-02
**Purpose**: Complete verification of the entire MVP pipeline with interactive credential validation
**Execute from**: `~/Dropbox/ALOMA/claude-code/weekly-ai-sigint/`
**Estimated Duration**: 5-10 minutes

---

## Prerequisites

Before executing, read best practices from:
```
~/Dropbox/ALOMA/claude-code/CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md
```

⚠️ **IMPORTANT**: This file MUST be executed from `~/Dropbox/ALOMA/claude-code/weekly-ai-sigint/`

---

## Pre-Flight: Credential Validation & Setup

This section validates all API credentials BEFORE running tests. Claude Code will prompt you to enter any missing or invalid keys.

### Step 1: Verify Working Directory

```bash
cd ~/Dropbox/ALOMA/claude-code/weekly-ai-sigint
pwd
# Expected: /Users/pwilliamson/Dropbox/ALOMA/claude-code/weekly-ai-sigint
```

### Step 2: Activate Virtual Environment

```bash
source venv/bin/activate
which python
# Expected: .../weekly-ai-sigint/venv/bin/python
```

### Step 3: Validate ANTHROPIC_API_KEY (Required)

```bash
echo "=== Validating ANTHROPIC_API_KEY ==="
ANTHROPIC_KEY=$(grep "^ANTHROPIC_API_KEY=" .env | cut -d= -f2 | tr -d '"' | tr -d "'")
KEY_LENGTH=${#ANTHROPIC_KEY}
echo "Key length: $KEY_LENGTH characters"
echo "Key prefix: ${ANTHROPIC_KEY:0:12}..."
```

**Validation criteria:**
- Length must be 100+ characters
- Must start with `sk-ant-api03-`

**If invalid or missing, STOP and prompt user:**

> 🔑 **ANTHROPIC_API_KEY is missing or invalid.**
>
> **How to obtain:**
> 1. Go to https://console.anthropic.com/
> 2. Sign in or create an account
> 3. Navigate to **API Keys** in the left sidebar
> 4. Click **Create Key**
> 5. Copy the key (starts with `sk-ant-api03-`)
>
> **Please provide your Anthropic API key:**

After user provides key, update .env:

```bash
# Remove old key if exists
grep -v "^ANTHROPIC_API_KEY=" .env > .env.tmp && mv .env.tmp .env

# Add new key (replace YOUR_KEY_HERE with actual key)
echo 'ANTHROPIC_API_KEY=YOUR_KEY_HERE' >> .env

# Verify
grep "^ANTHROPIC_API_KEY=" .env | cut -d= -f2 | head -c 20
echo "... (key set)"
```

### Step 4: Validate NOTION_TOKEN (Optional)

```bash
echo "=== Validating NOTION_TOKEN ==="
NOTION_TOKEN=$(grep "^NOTION_TOKEN=" .env | cut -d= -f2 | tr -d '"' | tr -d "'")
TOKEN_LENGTH=${#NOTION_TOKEN}
echo "Token length: $TOKEN_LENGTH characters"
if [ "$TOKEN_LENGTH" -gt 10 ]; then
    echo "Token prefix: ${NOTION_TOKEN:0:10}..."
fi
```

**Validation criteria:**
- Length should be 50+ characters
- Typically starts with `secret_` or `ntn_`

**If missing or user wants to add, prompt:**

> 🔑 **NOTION_TOKEN is missing or invalid.**
>
> **How to obtain:**
> 1. Go to https://www.notion.so/my-integrations
> 2. Click **+ New integration**
> 3. Name it (e.g., "Weekly AI Sigint")
> 4. Select your workspace
> 5. Click **Submit**
> 6. Copy the **Internal Integration Token** (starts with `secret_` or `ntn_`)
> 7. **Important**: Share your target Notion page with this integration!
>
> **Enter your Notion token (or press Enter to skip Notion integration):**

After user provides token, update .env:

```bash
# Remove old token if exists
grep -v "^NOTION_TOKEN=" .env > .env.tmp && mv .env.tmp .env

# Add new token
echo 'NOTION_TOKEN=YOUR_TOKEN_HERE' >> .env
```

### Step 5: Validate NOTION_PAGE_ID (Optional, required if NOTION_TOKEN set)

```bash
echo "=== Validating NOTION_PAGE_ID ==="
NOTION_PAGE_ID=$(grep "^NOTION_PAGE_ID=" .env | cut -d= -f2 | tr -d '"' | tr -d "'")
echo "Page ID: $NOTION_PAGE_ID"
echo "Page ID length: ${#NOTION_PAGE_ID} characters"
```

**Validation criteria:**
- Should be 32 characters (UUID without dashes) or 36 characters (UUID with dashes)

**If missing and NOTION_TOKEN is set, prompt:**

> 🔑 **NOTION_PAGE_ID is missing.**
>
> **How to obtain:**
> 1. Open the Notion page where briefings should be published
> 2. Click **Share** → **Copy link**
> 3. The URL looks like: `https://www.notion.so/Your-Page-Title-abc123def456...`
> 4. The page ID is the 32-character string at the end (after the last hyphen)
> 5. Example: `abc123def456789012345678901234ab`
>
> **Enter your Notion page ID:**

After user provides page ID, update .env:

```bash
grep -v "^NOTION_PAGE_ID=" .env > .env.tmp && mv .env.tmp .env
echo 'NOTION_PAGE_ID=YOUR_PAGE_ID_HERE' >> .env
```

### Step 6: Validate SLACK_WEBHOOK_URL (Optional)

```bash
echo "=== Validating SLACK_WEBHOOK_URL ==="
SLACK_URL=$(grep "^SLACK_WEBHOOK_URL=" .env | cut -d= -f2 | tr -d '"' | tr -d "'")
echo "Webhook URL length: ${#SLACK_URL} characters"
if [ "${#SLACK_URL}" -gt 20 ]; then
    echo "URL prefix: ${SLACK_URL:0:35}..."
fi
```

**Validation criteria:**
- Must start with `https://hooks.slack.com/services/`
- Length typically 70-100+ characters

**If missing or user wants to add, prompt:**

> 🔑 **SLACK_WEBHOOK_URL is missing or invalid.**
>
> **How to obtain:**
> 1. Go to https://api.slack.com/apps
> 2. Click **Create New App** → **From scratch**
> 3. Name it (e.g., "Weekly AI Sigint") and select your workspace
> 4. In the left sidebar, click **Incoming Webhooks**
> 5. Toggle **Activate Incoming Webhooks** to ON
> 6. Click **Add New Webhook to Workspace**
> 7. Select the channel for notifications
> 8. Copy the **Webhook URL** (starts with `https://hooks.slack.com/services/`)
>
> **Enter your Slack webhook URL (or press Enter to skip Slack integration):**

After user provides URL, update .env:

```bash
grep -v "^SLACK_WEBHOOK_URL=" .env > .env.tmp && mv .env.tmp .env
echo 'SLACK_WEBHOOK_URL=YOUR_WEBHOOK_URL_HERE' >> .env
```

### Step 7: Final Credential Summary

```bash
echo "=== Credential Summary ==="
echo ""
ANTH=$(grep "^ANTHROPIC_API_KEY=" .env | cut -d= -f2)
NOTION=$(grep "^NOTION_TOKEN=" .env | cut -d= -f2)
PAGE=$(grep "^NOTION_PAGE_ID=" .env | cut -d= -f2)
SLACK=$(grep "^SLACK_WEBHOOK_URL=" .env | cut -d= -f2)

if [ ${#ANTH} -gt 100 ]; then echo "✅ ANTHROPIC_API_KEY: Valid (${#ANTH} chars)"; else echo "❌ ANTHROPIC_API_KEY: INVALID - Tests will fail"; fi
if [ ${#NOTION} -gt 40 ]; then echo "✅ NOTION_TOKEN: Valid (${#NOTION} chars)"; else echo "⏭️  NOTION_TOKEN: Not set - Stage 5 will be skipped"; fi
if [ ${#PAGE} -gt 20 ]; then echo "✅ NOTION_PAGE_ID: Valid (${#PAGE} chars)"; else echo "⏭️  NOTION_PAGE_ID: Not set - Stage 5 will be skipped"; fi
if [ ${#SLACK} -gt 50 ]; then echo "✅ SLACK_WEBHOOK_URL: Valid (${#SLACK} chars)"; else echo "⏭️  SLACK_WEBHOOK_URL: Not set - Stage 6 will be skipped"; fi
echo ""
```

**Do not proceed if ANTHROPIC_API_KEY is invalid.**

---

## Pre-Flight: Server Setup

```bash
echo "=== Server Setup ==="

# Kill any existing server on port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
echo "Cleared port 8000"

# Verify database directory exists
mkdir -p data
echo "Data directory ready"

# Start server
source venv/bin/activate
uvicorn app.main:app --port 8000 > /tmp/e2e-test.log 2>&1 &
echo "Server starting..."

# Wait for server
sleep 4

# Verify health
curl -s http://localhost:8000/health | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('Health check:', d.get('status', 'unknown'))
    if d.get('status') == 'healthy':
        print('✅ Server is ready')
    else:
        print('❌ Server not healthy')
except:
    print('❌ Server failed to start - check /tmp/e2e-test.log')
"
```

---

## Stage 1: Infrastructure Verification

### 1.1 All Pages Load

```bash
echo "=== Stage 1.1: Page Load Tests ==="
for page in "" "sources" "briefings" "settings" "prompt"; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/$page")
    if [ "$CODE" = "200" ]; then
        echo "✅ /$page: $CODE"
    else
        echo "❌ /$page: $CODE"
    fi
done
```

### 1.2 All API Endpoints Respond

```bash
echo "=== Stage 1.2: API Endpoint Tests ==="

# Sources API
curl -s http://localhost:8000/api/sources/ | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('✅ Sources API: ' + str(len(d)) + ' sources')
"

# Briefings API
curl -s http://localhost:8000/api/briefings/ | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('✅ Briefings API: ' + str(len(d)) + ' briefings')
"

# Settings API (fixed: no f-string with operator)
curl -s http://localhost:8000/api/settings/ | python3 -c "
import sys, json
d = json.load(sys.stdin)
has_key = bool(d.get('anthropic_api_key', ''))
print('✅ Settings API: Anthropic key set = ' + str(has_key))
"

# Prompt API
curl -s http://localhost:8000/api/prompt/ | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('✅ Prompt API: ' + str(d.get('word_count', 0)) + ' words')
"

# Scheduler API
curl -s http://localhost:8000/api/scheduler/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('✅ Scheduler API: running = ' + str(d.get('running', False)))
"
```

### 1.3 Scheduler Status

```bash
echo "=== Stage 1.3: Scheduler Status ==="
curl -s http://localhost:8000/api/scheduler/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Running: ' + str(d.get('running', False)))
print('Paused: ' + str(d.get('paused', False)))
print('Next run: ' + str(d.get('next_run', 'N/A')))
print('Job count: ' + str(d.get('job_count', 0)))
"
```

---

## Stage 2: Source Management

### 2.1 List Sources

```bash
echo "=== Stage 2.1: List Sources ==="
curl -s http://localhost:8000/api/sources/ | python3 -c "
import sys, json
sources = json.load(sys.stdin)
print('Total sources: ' + str(len(sources)))
for s in sources:
    status = '✅' if s.get('active', False) else '❌'
    name = s.get('name', 'Unknown')
    cat = s.get('category', 'unknown')
    url = s.get('url', '')[:50]
    print('  ' + status + ' ' + name + ' (' + cat + ') - ' + url + '...')
"
```

### 2.2 Create Test Source

```bash
echo "=== Stage 2.2: Create Test Source ==="
curl -s -X POST http://localhost:8000/api/sources/ -H "Content-Type: application/json" -d '{"name":"E2E Test Source","category":"newsletter","source_type":"rss","url":"https://e2e-test.example.com/feed","priority":5,"active":false}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('✅ Created source ID: ' + str(d.get('id', 'unknown')))
"
```

### 2.3 Delete Test Source

First, get the test source ID:

```bash
echo "=== Stage 2.3: Find Test Source ID ==="
curl -s http://localhost:8000/api/sources/ | python3 -c "
import sys, json
sources = json.load(sys.stdin)
matches = [s['id'] for s in sources if 'E2E Test' in s.get('name', '')]
if matches:
    print('Test source ID: ' + str(matches[0]))
else:
    print('No test source found')
"
```

Then delete it (replace ID with actual value from above):

```bash
echo "=== Stage 2.3: Delete Test Source ==="
# Replace 3 with actual ID from previous command
curl -s -X DELETE http://localhost:8000/api/sources/3 -w "\nHTTP Status: %{http_code}\n"
echo "✅ Test source deleted"
```

---

## Stage 3: Content Fetching

### 3.1 Fetch from All Sources

```bash
echo "=== Stage 3.1: Fetch Content ==="
echo "Fetching from all sources (may take 30-60 seconds)..."
curl -s -X POST "http://localhost:8000/api/run/fetch" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Status: ' + d.get('status', 'unknown'))
results = d.get('results', {})
for source, data in results.items():
    count = data.get('new_items', 0) if isinstance(data, dict) else 0
    print('  ' + source + ': ' + str(count) + ' new items')
"
```

### 3.2 Verify Content Count

```bash
echo "=== Stage 3.2: Content Count ==="
curl -s http://localhost:8000/api/content/ | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Total content items: ' + str(len(d)))
"
```

### 3.3 Recent Content Preview

```bash
echo "=== Stage 3.3: Recent Content ==="
curl -s "http://localhost:8000/api/content/?limit=5" | python3 -c "
import sys, json
items = json.load(sys.stdin)
print('Recent items (last 5):')
for item in items[:5]:
    title = item.get('title', 'No title')[:60]
    print('  - ' + title + '...')
"
```

---

## Stage 4: Briefing Synthesis

### 4.1 Synthesize Briefing

```bash
echo "=== Stage 4.1: Synthesize Briefing ==="
echo "Calling Claude API (may take 30-90 seconds)..."
curl -s -X POST "http://localhost:8000/api/run/synthesize?days_back=7" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'error' in d or 'detail' in d:
    print('❌ Error: ' + str(d.get('error', d.get('detail', 'Unknown error'))))
else:
    print('✅ Status: ' + d.get('status', 'unknown'))
    print('   Briefing ID: ' + str(d.get('briefing_id', 'N/A')))
"
```

### 4.2 Verify Briefing Created

```bash
echo "=== Stage 4.2: Verify Briefing ==="
curl -s http://localhost:8000/api/briefings/latest | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'detail' in d:
    print('❌ No briefing found: ' + d.get('detail', ''))
else:
    print('✅ Briefing ID: ' + str(d.get('id', 'N/A')))
    print('   Title: ' + str(d.get('title', 'N/A')))
    print('   Created: ' + str(d.get('created_at', 'N/A')))
    content = d.get('content', '')
    print('   Content length: ' + str(len(content)) + ' chars')
"
```

### 4.3 Briefing Preview

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

## Stage 5: Export to Notion

**Skip condition**: If NOTION_TOKEN or NOTION_PAGE_ID not set, skip this stage.

```bash
echo "=== Stage 5: Notion Export ==="
NOTION_TOKEN=$(grep "^NOTION_TOKEN=" .env | cut -d= -f2)
NOTION_PAGE=$(grep "^NOTION_PAGE_ID=" .env | cut -d= -f2)

if [ ${#NOTION_TOKEN} -lt 40 ] || [ ${#NOTION_PAGE} -lt 20 ]; then
    echo "⏭️  Skipping: NOTION_TOKEN or NOTION_PAGE_ID not configured"
else
    echo "Exporting to Notion..."
    curl -s -X POST http://localhost:8000/api/run/export/notion | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'error' in d or 'detail' in d:
    print('❌ Error: ' + str(d.get('error', d.get('detail', ''))))
else:
    print('✅ Exported to Notion')
    print('   URL: ' + str(d.get('notion_url', 'N/A')))
"
fi
```

---

## Stage 6: Slack Notification

**Skip condition**: If SLACK_WEBHOOK_URL not set, skip this stage.

```bash
echo "=== Stage 6: Slack Notification ==="
SLACK_URL=$(grep "^SLACK_WEBHOOK_URL=" .env | cut -d= -f2)

if [ ${#SLACK_URL} -lt 50 ]; then
    echo "⏭️  Skipping: SLACK_WEBHOOK_URL not configured"
else
    echo "Sending Slack notification..."
    curl -s -X POST http://localhost:8000/api/run/notify/slack | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'error' in d or 'detail' in d:
    print('❌ Error: ' + str(d.get('error', d.get('detail', ''))))
else:
    print('✅ Slack notification sent')
"
fi
```

---

## Stage 7: Scheduler Controls

### 7.1 Pause Scheduler

```bash
echo "=== Stage 7.1: Pause Scheduler ==="
curl -s -X POST http://localhost:8000/api/scheduler/pause | python3 -c "
import sys, json
d = json.load(sys.stdin)
success = d.get('success', False)
print('Paused: ' + str(success))
"

# Verify paused
curl -s http://localhost:8000/api/scheduler/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Status - Paused: ' + str(d.get('paused', False)))
"
```

### 7.2 Resume Scheduler

```bash
echo "=== Stage 7.2: Resume Scheduler ==="
curl -s -X POST http://localhost:8000/api/scheduler/resume | python3 -c "
import sys, json
d = json.load(sys.stdin)
success = d.get('success', False)
print('Resumed: ' + str(success))
"

# Verify running
curl -s http://localhost:8000/api/scheduler/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
running = d.get('running', False)
paused = d.get('paused', True)
print('Status - Running: ' + str(running) + ', Paused: ' + str(paused))
"
```

### 7.3 Job History

```bash
echo "=== Stage 7.3: Job History ==="
curl -s http://localhost:8000/api/scheduler/history | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('History count: ' + str(d.get('count', 0)))
for run in d.get('history', [])[:3]:
    started = run.get('started_at', 'N/A')
    success = run.get('success', 'N/A')
    print('  - ' + str(started) + ': success=' + str(success))
"
```

---

## Stage 8: Full Pipeline Test (Optional)

This runs the complete automated pipeline that the scheduler would execute.

```bash
echo "=== Stage 8: Full Pipeline (Manual Trigger) ==="
echo "This runs: Fetch → Synthesize → Notion → Slack"
echo "May take 2-3 minutes..."
curl -s -X POST http://localhost:8000/api/scheduler/run-now | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Pipeline result:')
print(json.dumps(d, indent=2))
"
```

---

## Stage 9: Error Log Check

```bash
echo "=== Stage 9: Error Log Check ==="
ERROR_COUNT=$(grep -ci "error\|exception\|traceback" /tmp/e2e-test.log || echo "0")
echo "Errors found: $ERROR_COUNT"

if [ "$ERROR_COUNT" != "0" ]; then
    echo ""
    echo "Recent errors:"
    grep -i "error\|exception\|traceback" /tmp/e2e-test.log | tail -10
fi
```

---

## Stage 10: Cleanup

```bash
echo "=== Stage 10: Cleanup ==="
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
echo "✅ Server stopped"
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
| Synthesize fails with 401 | Invalid API key | Re-run credential validation, get new key |
| Synthesize fails with 500 | API key format wrong | Ensure key starts with `sk-ant-api03-` |
| Notion export fails | Invalid token or page ID | Verify token, ensure page shared with integration |
| Slack fails | Invalid webhook URL | Verify URL starts with `https://hooks.slack.com/services/` |
| Scheduler not running | Lifespan not triggering | Check app/main.py lifespan function |
| 500 errors | Code bug | Check /tmp/e2e-test.log for traceback |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-01-02 | Added interactive credential validation with prompts. Fixed bash escaping issues (no subshell assignment, no f-string operators). Added skip logic for optional integrations. |
| 1.0 | 2026-01-02 | Initial version |
