# Weekly AI Sigint — Phase 5C Verification Tests

> Run these tests to verify the Briefings Viewer UI functionality.

## Pre-Flight

```bash
# Verify working directory
pwd  # Should be weekly-ai-sigint

# Kill any existing server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# Start server
source venv/bin/activate
uvicorn app.main:app --port 8000 > /tmp/phase5c-tests.log 2>&1 &
sleep 3

# Verify server is running
curl -s http://localhost:8000/health
```

---

## 1. Briefings Page Renders

```bash
# Verify page loads
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/briefings
# Expected: 200

# Verify key UI elements exist
curl -s http://localhost:8000/briefings | grep -c "Briefing History"
# Expected: >= 1

curl -s http://localhost:8000/briefings | grep -c "briefings-list"
# Expected: >= 1
```

---

## 2. List Briefings API (GET)

```bash
# Get all briefings
curl -s http://localhost:8000/api/briefings/ | python3 -m json.tool

# Count briefings
curl -s http://localhost:8000/api/briefings/ | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'Briefings: {len(data)}')"
```

---

## 3. Get Latest Briefing

```bash
# Get latest briefing (may be 404 if none exist)
curl -s http://localhost:8000/api/briefings/latest -w "\nHTTP Status: %{http_code}\n"
# Expected: 200 with briefing data, or 404 if no briefings
```

---

## 4. Create Test Briefing (for testing)

Since briefings are normally created via synthesis, we need to create one directly for testing:

```bash
# Check if any briefings exist
BRIEFING_COUNT=$(curl -s http://localhost:8000/api/briefings/ | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
echo "Current briefing count: $BRIEFING_COUNT"

# If no briefings, create one via database (workaround for testing)
# This would normally be done via POST /api/run/synthesize
```

**Note**: If no briefings exist, the UI should show an empty state. The full CRUD tests require a briefing to exist, which is created via the synthesize endpoint (requires valid Anthropic API key).

---

## 5. Get Single Briefing (GET by ID)

```bash
# Get briefing by ID (adjust ID based on what exists)
curl -s http://localhost:8000/api/briefings/1 -w "\nHTTP Status: %{http_code}\n"
# Expected: 200 with briefing data, or 404 if not found
```

---

## 6. Delete Briefing (DELETE)

```bash
# Delete briefing by ID (use a test briefing ID)
# WARNING: This will permanently delete the briefing
curl -s -X DELETE http://localhost:8000/api/briefings/999 -w "\nHTTP Status: %{http_code}\n"
# Expected: 404 for non-existent, 200/204 for existing
```

---

## 7. Export to Notion Endpoint

```bash
# Test Notion export endpoint (requires valid credentials)
curl -s -X POST http://localhost:8000/api/run/export/notion -w "\nHTTP Status: %{http_code}\n"
# Expected: 400 "No briefing found" if no briefings, or success/error based on credentials
```

---

## 8. Slack Notification Endpoint

```bash
# Test Slack notify endpoint (requires valid webhook)
curl -s -X POST http://localhost:8000/api/run/notify/slack -w "\nHTTP Status: %{http_code}\n"
# Expected: 400 "No briefing found" if no briefings, or success/error based on credentials
```

---

## 9. Error Handling

```bash
# Try to get non-existent briefing
curl -s http://localhost:8000/api/briefings/99999 -w "\nHTTP Status: %{http_code}\n"
# Expected: 404

# Try to delete non-existent briefing
curl -s -X DELETE http://localhost:8000/api/briefings/99999 -w "\nHTTP Status: %{http_code}\n"
# Expected: 404
```

---

## 10. Check Server Logs for Errors

```bash
# Check for any errors during tests
cat /tmp/phase5c-tests.log | grep -i "error\|exception\|traceback" | head -10
# Expected: No errors (empty output)
```

---

## 11. Cleanup

```bash
# Stop test server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
echo "✅ Server stopped"
```

---

## Summary Checklist

After running all tests, verify:

- [ ] Briefings page renders (200 status)
- [ ] GET /api/briefings/ returns list (may be empty)
- [ ] GET /api/briefings/latest returns briefing or 404
- [ ] GET /api/briefings/{id} returns briefing or 404
- [ ] DELETE /api/briefings/{id} works or returns 404
- [ ] Export/notify endpoints respond appropriately
- [ ] Empty state displays correctly (if no briefings)
- [ ] No errors in server logs

---

## Browser Verification (Manual)

Open http://localhost:8000/briefings in browser and verify:

1. [ ] Page shows "Briefing History" header
2. [ ] Empty state message if no briefings
3. [ ] List displays briefings if they exist
4. [ ] Click on briefing opens detail modal
5. [ ] Modal shows full content with markdown rendering
6. [ ] Export to Notion button visible (disabled if already exported)
7. [ ] Send to Slack button visible (disabled if already sent)
8. [ ] Delete button shows confirmation dialog
9. [ ] Loading states appear during operations

---

## Quick All-in-One Test Script

Run this single block to test basic functionality:

```bash
echo "=== Phase 5C API Tests ===" && lsof -ti :8000 | xargs kill -9 2>/dev/null; source venv/bin/activate && uvicorn app.main:app --port 8000 > /tmp/test.log 2>&1 & sleep 3 && echo "1. Health:" && curl -s http://localhost:8000/health | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])" && echo "2. Page status:" && curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/briefings && echo "3. List briefings:" && curl -s http://localhost:8000/api/briefings/ | python3 -c "import sys,json;print(f'Count: {len(json.load(sys.stdin))}')" && echo "4. Latest:" && curl -s http://localhost:8000/api/briefings/latest | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('title','No briefings') if 'title' in d else d.get('detail','Error'))" && echo "5. Errors:" && cat /tmp/test.log | grep -ci "error" | xargs -I {} bash -c '[ {} -eq 0 ] && echo "✅ No errors" || echo "⚠️ {} errors found"' && lsof -ti :8000 | xargs kill -9 2>/dev/null && echo "=== Tests Complete ==="
```

---

## Full Integration Test (When Briefing Exists)

After running synthesis with valid API key, test the full flow:

```bash
# 1. Run synthesis first (requires ANTHROPIC_API_KEY)
curl -s -X POST "http://localhost:8000/api/run/synthesize?days_back=30" | python3 -m json.tool

# 2. Get the new briefing
curl -s http://localhost:8000/api/briefings/latest | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'ID: {d[\"id\"]}, Title: {d[\"title\"]}')"

# 3. Test export to Notion (requires NOTION_TOKEN)
curl -s -X POST http://localhost:8000/api/run/export/notion | python3 -m json.tool

# 4. Test Slack notification (requires SLACK_WEBHOOK_URL)
curl -s -X POST http://localhost:8000/api/run/notify/slack | python3 -m json.tool

# 5. Verify export status updated
curl -s http://localhost:8000/api/briefings/latest | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'Notion URL: {d.get(\"notion_url\",\"Not exported\")}')"
```
