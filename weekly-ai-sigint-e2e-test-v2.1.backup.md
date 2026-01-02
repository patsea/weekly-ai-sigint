# Weekly AI Sigint — Full End-to-End Test (v2.1)

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

## CLAUDE CODE EXECUTION INSTRUCTIONS

**This file requires interactive credential validation.**

When executing this file, Claude Code MUST:
1. Run each credential validation command
2. Check the output for VALID/INVALID/MISSING status
3. **If ANY credential is INVALID or MISSING**: Stop, show the user how to obtain it, ask them to provide it, update .env, and re-validate
4. **Do NOT skip optional credentials without explicitly asking the user** if they want to configure them
5. Only proceed to the test stages after ALL credentials have been validated or explicitly skipped by user choice

---

## Phase 1: Working Directory Setup

```bash
cd ~/Dropbox/ALOMA/claude-code/weekly-ai-sigint
pwd
```

**Expected**: `/Users/pwilliamson/Dropbox/ALOMA/claude-code/weekly-ai-sigint`

```bash
source venv/bin/activate
which python
```

**Expected**: Path ending in `weekly-ai-sigint/venv/bin/python`

---

## Phase 2: Credential Validation (Interactive)

### 2.1 Validate ANTHROPIC_API_KEY (Required)

```bash
echo "=== ANTHROPIC_API_KEY Validation ==="
KEY=$(grep "^ANTHROPIC_API_KEY=" .env 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
LEN=${#KEY}
if [ "$LEN" -gt 100 ]; then
    PREFIX="${KEY:0:15}"
    if [[ "$PREFIX" == sk-ant-api03-* ]]; then
        echo "STATUS: VALID"
        echo "Length: $LEN characters"
        echo "Prefix: ${KEY:0:15}..."
    else
        echo "STATUS: INVALID (wrong prefix)"
        echo "Length: $LEN characters"
        echo "Expected prefix: sk-ant-api03-"
        echo "Actual prefix: ${KEY:0:15}"
    fi
else
    echo "STATUS: MISSING or TOO SHORT"
    echo "Length: $LEN characters (need 100+)"
fi
```

#### CLAUDE CODE: CHECK OUTPUT AND ACT

**If STATUS is VALID**: Proceed to 2.2

**If STATUS is INVALID or MISSING**: You MUST stop and do the following:

1. Tell the user their Anthropic API key is missing or invalid
2. Provide these instructions:

> **How to obtain your Anthropic API key:**
> 1. Go to https://console.anthropic.com/
> 2. Sign in or create an account
> 3. Navigate to **API Keys** in the left sidebar
> 4. Click **Create Key**
> 5. Copy the key (it starts with `sk-ant-api03-`)
>
> Please paste your Anthropic API key:

3. Wait for user to provide the key
4. Run this command to update .env (replace `PASTE_KEY_HERE` with actual key):

```bash
grep -v "^ANTHROPIC_API_KEY=" .env > .env.tmp 2>/dev/null || touch .env.tmp
mv .env.tmp .env
echo 'ANTHROPIC_API_KEY=PASTE_KEY_HERE' >> .env
```

5. Re-run the validation command above to confirm STATUS: VALID
6. Do NOT proceed until ANTHROPIC_API_KEY shows STATUS: VALID

---

### 2.2 Validate NOTION_TOKEN (Optional)

```bash
echo "=== NOTION_TOKEN Validation ==="
TOKEN=$(grep "^NOTION_TOKEN=" .env 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
LEN=${#TOKEN}
if [ "$LEN" -gt 40 ]; then
    echo "STATUS: VALID"
    echo "Length: $LEN characters"
    echo "Prefix: ${TOKEN:0:10}..."
else
    echo "STATUS: MISSING or TOO SHORT"
    echo "Length: $LEN characters (need 40+)"
fi
```

#### CLAUDE CODE: CHECK OUTPUT AND ACT

**If STATUS is VALID**: Proceed to 2.3

**If STATUS is MISSING**: You MUST ask the user:

> **NOTION_TOKEN is not configured.**
>
> Notion integration allows briefings to be automatically published to a Notion page.
>
> Would you like to configure Notion integration? (yes/no)

**If user says YES**, provide these instructions:

> **How to obtain your Notion integration token:**
> 1. Go to https://www.notion.so/my-integrations
> 2. Click **+ New integration**
> 3. Name it (e.g., "Weekly AI Sigint")
> 4. Select your workspace
> 5. Click **Submit**
> 6. Copy the **Internal Integration Token** (starts with `secret_` or `ntn_`)
> 7. **Important**: You must also share your target Notion page with this integration!
>
> Please paste your Notion integration token:

Then update .env:

```bash
grep -v "^NOTION_TOKEN=" .env > .env.tmp 2>/dev/null || touch .env.tmp
mv .env.tmp .env
echo 'NOTION_TOKEN=PASTE_TOKEN_HERE' >> .env
```

Re-run validation to confirm STATUS: VALID before proceeding.

**If user says NO**: Note that Stage 5 (Notion Export) will be skipped, then proceed to 2.4 (skip 2.3).

---

### 2.3 Validate NOTION_PAGE_ID (Required if NOTION_TOKEN is set)

**Only run this if NOTION_TOKEN was configured.**

```bash
echo "=== NOTION_PAGE_ID Validation ==="
PAGE_ID=$(grep "^NOTION_PAGE_ID=" .env 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
LEN=${#PAGE_ID}
if [ "$LEN" -ge 32 ]; then
    echo "STATUS: VALID"
    echo "Page ID: $PAGE_ID"
else
    echo "STATUS: MISSING or TOO SHORT"
    echo "Length: $LEN characters (need 32+)"
fi
```

#### CLAUDE CODE: CHECK OUTPUT AND ACT

**If STATUS is VALID**: Proceed to 2.4

**If STATUS is MISSING** (and NOTION_TOKEN was set): You MUST provide these instructions:

> **NOTION_PAGE_ID is required for Notion integration.**
>
> **How to obtain your Notion page ID:**
> 1. Open the Notion page where briefings should be published
> 2. Click **Share** → **Copy link**
> 3. The URL looks like: `https://www.notion.so/Your-Page-Title-abc123def456...`
> 4. The page ID is the 32-character string at the end (after the last hyphen, before any `?`)
> 5. Example: If URL ends with `Weekly-Briefings-abc123def456789012345678901234ab`
>    → Page ID is `abc123def456789012345678901234ab`
>
> **Important**: Make sure you've shared this page with your integration!
> (Open page → Share → Invite → Select your integration)
>
> Please paste your Notion page ID:

Then update .env:

```bash
grep -v "^NOTION_PAGE_ID=" .env > .env.tmp 2>/dev/null || touch .env.tmp
mv .env.tmp .env
echo 'NOTION_PAGE_ID=PASTE_PAGE_ID_HERE' >> .env
```

Re-run validation to confirm STATUS: VALID before proceeding.

---

### 2.4 Validate SLACK_WEBHOOK_URL (Optional)

```bash
echo "=== SLACK_WEBHOOK_URL Validation ==="
URL=$(grep "^SLACK_WEBHOOK_URL=" .env 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
LEN=${#URL}
if [ "$LEN" -gt 70 ]; then
    if [[ "$URL" == https://hooks.slack.com/services/* ]]; then
        echo "STATUS: VALID"
        echo "Length: $LEN characters"
        echo "URL prefix: ${URL:0:40}..."
    else
        echo "STATUS: INVALID (wrong format)"
        echo "Expected: https://hooks.slack.com/services/..."
        echo "Got: ${URL:0:40}..."
    fi
else
    echo "STATUS: MISSING or TOO SHORT"
    echo "Length: $LEN characters (need 70+)"
fi
```

#### CLAUDE CODE: CHECK OUTPUT AND ACT

**If STATUS is VALID**: Proceed to Phase 3

**If STATUS is MISSING or INVALID**: You MUST ask the user:

> **SLACK_WEBHOOK_URL is not configured.**
>
> Slack integration sends a notification to a Slack channel when a new briefing is ready.
>
> Would you like to configure Slack notifications? (yes/no)

**If user says YES**, provide these instructions:

> **How to obtain your Slack webhook URL:**
> 1. Go to https://api.slack.com/apps
> 2. Click **Create New App** → **From scratch**
> 3. Name it (e.g., "Weekly AI Sigint") and select your workspace
> 4. Click **Create App**
> 5. In the left sidebar, click **Incoming Webhooks**
> 6. Toggle **Activate Incoming Webhooks** to ON
> 7. Scroll down and click **Add New Webhook to Workspace**
> 8. Select the channel where notifications should go
> 9. Click **Allow**
> 10. Copy the **Webhook URL** (starts with `https://hooks.slack.com/services/`)
>
> Please paste your Slack webhook URL:

Then update .env:

```bash
grep -v "^SLACK_WEBHOOK_URL=" .env > .env.tmp 2>/dev/null || touch .env.tmp
mv .env.tmp .env
echo 'SLACK_WEBHOOK_URL=PASTE_URL_HERE' >> .env
```

Re-run validation to confirm STATUS: VALID before proceeding.

**If user says NO**: Note that Stage 6 (Slack Notification) will be skipped, then proceed to Phase 3.

---

### 2.5 Credential Summary

After all credentials have been validated or skipped, run this summary:

```bash
echo "=== CREDENTIAL SUMMARY ==="
echo ""

ANTH=$(grep "^ANTHROPIC_API_KEY=" .env 2>/dev/null | cut -d= -f2)
NOTION=$(grep "^NOTION_TOKEN=" .env 2>/dev/null | cut -d= -f2)
PAGE=$(grep "^NOTION_PAGE_ID=" .env 2>/dev/null | cut -d= -f2)
SLACK=$(grep "^SLACK_WEBHOOK_URL=" .env 2>/dev/null | cut -d= -f2)

if [ ${#ANTH} -gt 100 ]; then echo "✅ ANTHROPIC_API_KEY: Configured"; else echo "❌ ANTHROPIC_API_KEY: MISSING (tests will fail)"; fi
if [ ${#NOTION} -gt 40 ]; then echo "✅ NOTION_TOKEN: Configured"; else echo "⏭️  NOTION_TOKEN: Skipped"; fi
if [ ${#PAGE} -gt 30 ]; then echo "✅ NOTION_PAGE_ID: Configured"; else echo "⏭️  NOTION_PAGE_ID: Skipped"; fi
if [ ${#SLACK} -gt 70 ]; then echo "✅ SLACK_WEBHOOK_URL: Configured"; else echo "⏭️  SLACK_WEBHOOK_URL: Skipped"; fi
echo ""
```

#### CLAUDE CODE: GATE CHECK

**Do NOT proceed to Phase 3 unless ANTHROPIC_API_KEY shows ✅ Configured.**

If it shows ❌ MISSING, go back to section 2.1 and resolve it first.

---

## Phase 3: Server Setup

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
    status = d.get('status', 'unknown')
    print('Health check: ' + status)
    if status == 'healthy':
        print('✅ Server is ready')
    else:
        print('❌ Server not healthy')
except Exception as e:
    print('❌ Server failed to start - check /tmp/e2e-test.log')
    print('Error: ' + str(e))
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

# Settings API
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
    print('Test source ID to delete: ' + str(matches[0]))
else:
    print('No test source found')
"
```

**CLAUDE CODE**: Note the ID from the output above, then run the delete command with that ID:

```bash
echo "=== Deleting Test Source ==="
curl -s -X DELETE http://localhost:8000/api/sources/REPLACE_WITH_ID -w "\nHTTP Status: %{http_code}\n"
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

**CLAUDE CODE**: Check the credential summary from Phase 2.5. If NOTION_TOKEN showed "⏭️ Skipped", skip this stage entirely and proceed to Stage 6.

```bash
echo "=== Stage 5: Notion Export ==="
echo "Exporting to Notion..."
curl -s -X POST http://localhost:8000/api/run/export/notion | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'error' in d or 'detail' in d:
    print('❌ Error: ' + str(d.get('error', d.get('detail', ''))))
else:
    print('✅ Exported to Notion')
    url = d.get('notion_url', d.get('url', 'N/A'))
    print('   URL: ' + str(url))
"
```

---

## Stage 6: Slack Notification

**CLAUDE CODE**: Check the credential summary from Phase 2.5. If SLACK_WEBHOOK_URL showed "⏭️ Skipped", skip this stage entirely and proceed to Stage 7.

```bash
echo "=== Stage 6: Slack Notification ==="
echo "Sending Slack notification..."
curl -s -X POST http://localhost:8000/api/run/notify/slack | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'error' in d or 'detail' in d:
    print('❌ Error: ' + str(d.get('error', d.get('detail', ''))))
else:
    print('✅ Slack notification sent')
"
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

## Stage 8: Error Log Check

```bash
echo "=== Stage 8: Error Log Check ==="
ERROR_COUNT=$(grep -ci "error\|exception\|traceback" /tmp/e2e-test.log || echo "0")
echo "Errors found: $ERROR_COUNT"

if [ "$ERROR_COUNT" != "0" ]; then
    echo ""
    echo "Recent errors:"
    grep -i "error\|exception\|traceback" /tmp/e2e-test.log | tail -10
fi
```

---

## Stage 9: Cleanup

```bash
echo "=== Stage 9: Cleanup ==="
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
echo "✅ Server stopped"
```

---

## E2E Test Summary

After running all stages, verify:

### Infrastructure
- [ ] All 5 pages load (200 status)
- [ ] All API endpoints respond
- [ ] Scheduler is running

### Data Flow
- [ ] Sources can be listed/created/deleted
- [ ] Content can be fetched
- [ ] Briefing can be synthesized

### Exports (if configured)
- [ ] Notion export succeeds (if configured)
- [ ] Slack notification succeeds (if configured)

### Scheduler
- [ ] Can pause/resume
- [ ] Status shows next run time

---

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| Synthesize fails with 401 | Invalid API key | Re-run Phase 2.1, get new key from console |
| Synthesize fails with 500 | API key format wrong | Key must start with `sk-ant-api03-` |
| Notion export fails | Token invalid or page not shared | Verify token, share page with integration |
| Slack fails | Webhook URL invalid | URL must start with `https://hooks.slack.com/services/` |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 2.1 | 2026-01-02 | Fixed credential validation to use explicit CLAUDE CODE directives. Added GATE CHECK sections. Made prompts mandatory, not optional documentation. |
| 2.0 | 2026-01-02 | Added interactive credential validation. Fixed bash escaping issues. |
| 1.0 | 2026-01-02 | Initial version |
