# Slack Integration Guide

## Setup

### Step 1: Create Incoming Webhook

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. Name: "AI SIGINT Bot", select your workspace
4. Go to **Incoming Webhooks** in sidebar
5. Toggle **Activate Incoming Webhooks** ON
6. Click **Add New Webhook to Workspace**
7. Select channel (e.g., `#ai-news`)
8. Copy the webhook URL

### Step 2: Configure

Add to `.env`:
```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Step 3: Test

```bash
curl -X POST http://localhost:8000/api/settings/test-connections \
  -H "Content-Type: application/json" \
  -d '{"test_slack": true}'
```

## Message Format

Briefings are delivered as rich Slack blocks:

```
🤖 Weekly AI SIGINT Briefing
━━━━━━━━━━━━━━━━━━━━━━━━━━

📰 Top Insights
1. OpenAI releases GPT-5...
2. Google announces Gemini 2.0...
3. Meta open-sources new model...

📊 Key Trends
• Increased focus on AI safety
• More efficient training methods
• Multimodal capabilities expanding

🔗 Full briefing: [View in Notion]
```

## Customization

Modify message format in `app/services/exporter.py`:

```python
def format_slack_message(briefing: Briefing) -> dict:
    # Customize blocks here
    ...
```
