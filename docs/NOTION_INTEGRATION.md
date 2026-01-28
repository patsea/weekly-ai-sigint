# Notion Integration Guide

## Setup

### Step 1: Create Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **+ New integration**
3. Name: "AI SIGINT"
4. Select workspace
5. Copy the **Internal Integration Token**

### Step 2: Create Target Database

Create a Notion database with these properties:

| Property | Type | Description |
|----------|------|-------------|
| Title | Title | Briefing title |
| Date | Date | Briefing date |
| Status | Select | Draft/Published |
| Content | Rich text | Briefing content |
| Sources | Number | Source count |

### Step 3: Share Database

1. Open your database in Notion
2. Click **Share** → **Invite**
3. Search for "AI SIGINT" integration
4. Click **Invite**

### Step 4: Configure

Get the database ID from the URL:
```
https://notion.so/myworkspace/abc123def456...
                              ^^^^^^^^^^^^^^
                              This is the database ID
```

Add to `.env`:
```
NOTION_TOKEN=secret_abc123...
NOTION_DATABASE_ID=abc123def456...
```

### Step 5: Test

```bash
curl -X POST http://localhost:8000/api/settings/test-connections \
  -H "Content-Type: application/json" \
  -d '{"test_notion": true}'
```

## Exported Format

Each briefing creates a new Notion page:

- **Title**: "AI SIGINT - {date}"
- **Content**: Full briefing with formatting
- **Properties**: Metadata (date, source count, etc.)
