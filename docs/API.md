# API Reference

Base URL: `http://localhost:8000`

## Health

### GET /health

Check server health and scheduler status.

**Response:**
```json
{
  "status": "healthy",
  "service": "weekly-ai-sigint",
  "scheduler": {
    "running": true,
    "next_run": "2024-01-21T06:00:00+00:00"
  }
}
```

---

## Sources

### GET /api/sources/

List all content sources.

**Response:** `200 OK`

### POST /api/sources/

Create a new source.

**Request:**
```json
{
  "name": "Source Name",
  "category": "newsletter",
  "source_type": "rss",
  "url": "https://example.com/feed",
  "priority": 5,
  "active": true
}
```

**Response:** `201 Created`

### GET /api/sources/{id}

Get a single source by ID.

**Response:** `200 OK` or `404 Not Found`

### PATCH /api/sources/{id}

Update a source.

**Request:** Partial source object

**Response:** `200 OK`

### DELETE /api/sources/{id}

Delete a source.

**Response:** `204 No Content` or `404 Not Found`

---

## Content

### GET /api/content/

List content items.

**Query Parameters:**
- `limit` (int): Maximum items to return (default: 100)
- `source_id` (int): Filter by source

**Response:** `200 OK`

---

## Briefings

### GET /api/briefings/

List all briefings.

**Response:** `200 OK`

### GET /api/briefings/latest

Get the most recent briefing.

**Response:** `200 OK` or `404 Not Found`

### GET /api/briefings/{id}

Get a specific briefing with full content.

**Response:** `200 OK`

### DELETE /api/briefings/{id}

Delete a briefing.

**Response:** `200 OK` or `404 Not Found`

---

## Manual Triggers

### POST /api/run/fetch

Fetch content from all active sources.

**Response:** `200 OK`
```json
{
  "success": true,
  "total_items": 15,
  "sources_fetched": 3
}
```

### POST /api/run/synthesize

Generate a new briefing from recent content.

**Query Parameters:**
- `days_back` (int): Days of content to include (default: 7)

**Response:** `200 OK`

### POST /api/run/export/notion

Export the latest briefing to Notion.

**Response:** `200 OK`

### POST /api/run/notify/slack

Send Slack notification for latest briefing.

**Response:** `200 OK`

---

## Settings

### GET /api/settings/

Get current settings (credentials masked).

**Response:** `200 OK`

### POST /api/settings/

Update settings (writes to .env file).

**Response:** `200 OK`

### POST /api/settings/test-connections

Test API credential validity.

**Response:** `200 OK`
```json
{
  "results": {
    "anthropic": true,
    "notion": true,
    "slack": false
  }
}
```

---

## Prompt

### GET /api/prompt/

Get current prompt template.

**Response:** `200 OK`

### POST /api/prompt/

Save updated prompt template.

**Request:**
```json
{
  "content": "# New prompt content..."
}
```

**Response:** `200 OK`

### POST /api/prompt/reset

Reset prompt to default template.

**Response:** `200 OK`

### GET /api/prompt/preview

Preview prompt with sample variables.

**Response:** `200 OK`

---

## Scheduler

### GET /api/scheduler/status

Get scheduler status.

**Response:** `200 OK`
```json
{
  "running": true,
  "paused": false,
  "next_run": "2024-01-21T06:00:00+00:00"
}
```

### POST /api/scheduler/pause

Pause scheduled jobs.

**Response:** `200 OK`

### POST /api/scheduler/resume

Resume scheduled jobs.

**Response:** `200 OK`

### POST /api/scheduler/run-now

Trigger full pipeline immediately.

**Response:** `200 OK`

### GET /api/scheduler/history

Get job execution history.

**Response:** `200 OK`
```json
{
  "history": [...],
  "count": 5
}
```
