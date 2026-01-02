# Weekly AI Sigint — Phase 5B Verification Tests

> Run these tests to verify the Sources Management UI JavaScript functionality.

## Pre-Flight

```bash
# Verify working directory
pwd  # Should be weekly-ai-sigint

# Kill any existing server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# Start server
source venv/bin/activate
uvicorn app.main:app --port 8000 > /tmp/phase5b-tests.log 2>&1 &
sleep 3

# Verify server is running
curl -s http://localhost:8000/health
```

---

## 1. Sources Page Renders

```bash
# Verify page loads
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/sources
# Expected: 200

# Verify key UI elements exist
curl -s http://localhost:8000/sources | grep -c "Add Source"
# Expected: >= 1

curl -s http://localhost:8000/sources | grep -c "sources-table-body"
# Expected: >= 1
```

---

## 2. List Existing Sources (GET)

```bash
# Get all sources
curl -s http://localhost:8000/api/sources/ | python3 -m json.tool

# Count sources
curl -s http://localhost:8000/api/sources/ | python3 -c "import sys,json; print(f'Sources: {len(json.load(sys.stdin))}')"
```

---

## 3. Create Source (POST)

```bash
# Create a test source (SINGLE LINE - Pitfall 25)
curl -s -X POST http://localhost:8000/api/sources/ -H "Content-Type: application/json" -d '{"name":"Phase5B Test Source","category":"newsletter","source_type":"rss","url":"https://phase5b-test.example.com/feed","priority":7,"active":true}' | python3 -m json.tool

# Verify it was created
curl -s http://localhost:8000/api/sources/ | grep -o "Phase5B Test Source"
# Expected: Phase5B Test Source
```

---

## 4. Get Single Source (GET by ID)

```bash
# Get the test source (adjust ID if needed)
curl -s http://localhost:8000/api/sources/ | python3 -c "import sys,json; sources=json.load(sys.stdin); test_src=[s for s in sources if 'Phase5B' in s.get('name','')]; print(test_src[0]['id'] if test_src else 'Not found')"

# Store ID for subsequent tests
TEST_ID=$(curl -s http://localhost:8000/api/sources/ | python3 -c "import sys,json; sources=json.load(sys.stdin); test_src=[s for s in sources if 'Phase5B' in s.get('name','')]; print(test_src[0]['id'] if test_src else '')")
echo "Test source ID: $TEST_ID"
```

---

## 5. Update Source (PATCH)

```bash
# Get the test source ID first
TEST_ID=$(curl -s http://localhost:8000/api/sources/ | python3 -c "import sys,json; sources=json.load(sys.stdin); test_src=[s for s in sources if 'Phase5B' in s.get('name','')]; print(test_src[0]['id'] if test_src else '')")

# Update priority (SINGLE LINE)
curl -s -X PATCH http://localhost:8000/api/sources/$TEST_ID -H "Content-Type: application/json" -d '{"priority":9}' | python3 -m json.tool

# Verify update
curl -s http://localhost:8000/api/sources/$TEST_ID | python3 -c "import sys,json; s=json.load(sys.stdin); print(f'Priority: {s.get(\"priority\")} (expected: 9)')"
```

---

## 6. Toggle Active Status (PATCH)

```bash
# Get current status
TEST_ID=$(curl -s http://localhost:8000/api/sources/ | python3 -c "import sys,json; sources=json.load(sys.stdin); test_src=[s for s in sources if 'Phase5B' in s.get('name','')]; print(test_src[0]['id'] if test_src else '')")

curl -s http://localhost:8000/api/sources/$TEST_ID | python3 -c "import sys,json; s=json.load(sys.stdin); print(f'Active: {s.get(\"active\")}')"

# Toggle to inactive (SINGLE LINE)
curl -s -X PATCH http://localhost:8000/api/sources/$TEST_ID -H "Content-Type: application/json" -d '{"active":false}' | python3 -m json.tool

# Verify toggle
curl -s http://localhost:8000/api/sources/$TEST_ID | python3 -c "import sys,json; s=json.load(sys.stdin); print(f'Active: {s.get(\"active\")} (expected: False)')"

# Toggle back to active
curl -s -X PATCH http://localhost:8000/api/sources/$TEST_ID -H "Content-Type: application/json" -d '{"active":true}' | python3 -m json.tool
```

---

## 7. Delete Source (DELETE)

```bash
# Get test source ID
TEST_ID=$(curl -s http://localhost:8000/api/sources/ | python3 -c "import sys,json; sources=json.load(sys.stdin); test_src=[s for s in sources if 'Phase5B' in s.get('name','')]; print(test_src[0]['id'] if test_src else '')")

# Delete the test source (SINGLE LINE)
curl -s -X DELETE http://localhost:8000/api/sources/$TEST_ID -w "\nHTTP Status: %{http_code}\n"
# Expected: HTTP Status: 200 or 204

# Verify deletion
curl -s http://localhost:8000/api/sources/ | grep -c "Phase5B Test Source"
# Expected: 0
```

---

## 8. Error Handling

```bash
# Try to get non-existent source
curl -s http://localhost:8000/api/sources/99999 -w "\nHTTP Status: %{http_code}\n"
# Expected: 404

# Try to delete non-existent source
curl -s -X DELETE http://localhost:8000/api/sources/99999 -w "\nHTTP Status: %{http_code}\n"
# Expected: 404

# Try invalid data
curl -s -X POST http://localhost:8000/api/sources/ -H "Content-Type: application/json" -d '{"name":""}' -w "\nHTTP Status: %{http_code}\n"
# Expected: 422 (validation error)
```

---

## 9. Check Server Logs for Errors

```bash
# Check for any errors during tests
cat /tmp/phase5b-tests.log | grep -i "error\|exception\|traceback" | head -10
# Expected: No errors (empty output)
```

---

## 10. Cleanup

```bash
# Stop test server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
echo "✅ Server stopped"
```

---

## Summary Checklist

After running all tests, verify:

- [ ] Sources page renders (200 status)
- [ ] GET /api/sources/ returns list
- [ ] POST /api/sources/ creates new source
- [ ] PATCH /api/sources/{id} updates source
- [ ] PATCH /api/sources/{id} toggles active status
- [ ] DELETE /api/sources/{id} removes source
- [ ] 404 returned for non-existent sources
- [ ] 422 returned for invalid data
- [ ] No errors in server logs

---

## Browser Verification (Manual)

Open http://localhost:8000/sources in browser and verify:

1. [ ] Table displays existing sources
2. [ ] "Add Source" button opens modal
3. [ ] Form submission creates new row
4. [ ] Edit button opens modal with existing data
5. [ ] Save updates row in table
6. [ ] Toggle button changes active status
7. [ ] Delete button shows confirmation
8. [ ] Confirm deletes row from table
9. [ ] Loading spinner appears during operations
10. [ ] Error messages display for failures

---

## Quick All-in-One Test Script

Run this single block to test all CRUD operations:

```bash
echo "=== Phase 5B API Tests ===" && lsof -ti :8000 | xargs kill -9 2>/dev/null; source venv/bin/activate && uvicorn app.main:app --port 8000 > /tmp/test.log 2>&1 & sleep 3 && echo "1. Health:" && curl -s http://localhost:8000/health | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])" && echo "2. Create:" && curl -s -X POST http://localhost:8000/api/sources/ -H "Content-Type: application/json" -d '{"name":"QuickTest","category":"newsletter","source_type":"rss","url":"https://quick.test/feed","priority":5,"active":true}' | python3 -c "import sys,json;print(f'Created ID: {json.load(sys.stdin).get(\"id\")}')" && TEST_ID=$(curl -s http://localhost:8000/api/sources/ | python3 -c "import sys,json;sources=json.load(sys.stdin);t=[s for s in sources if s.get('name')=='QuickTest'];print(t[0]['id'] if t else '')") && echo "3. Update:" && curl -s -X PATCH http://localhost:8000/api/sources/$TEST_ID -H "Content-Type: application/json" -d '{"priority":9}' | python3 -c "import sys,json;print(f'New priority: {json.load(sys.stdin).get(\"priority\")}')" && echo "4. Delete:" && curl -s -X DELETE http://localhost:8000/api/sources/$TEST_ID -w "Status: %{http_code}\n" && echo "5. Verify gone:" && curl -s http://localhost:8000/api/sources/ | grep -c "QuickTest" | xargs -I {} bash -c '[ {} -eq 0 ] && echo "✅ Deleted" || echo "❌ Still exists"' && echo "6. Errors:" && cat /tmp/test.log | grep -ci "error" | xargs -I {} bash -c '[ {} -eq 0 ] && echo "✅ No errors" || echo "⚠️ {} errors found"' && lsof -ti :8000 | xargs kill -9 2>/dev/null && echo "=== Tests Complete ==="
```
