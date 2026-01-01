# Weekly AI Sigint — Phase 5D Instructions

> Execute Phase 5D: Settings + Credentials UI

## Pre-Flight

```bash
# Verify working directory
pwd  # Should be weekly-ai-sigint

# Read best practices first
cat ~/Dropbox/ALOMA/claude-code/CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md | head -100

# Verify Phase 5C complete
ls -la app/templates/briefings.html

# Kill any existing server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
```

---

## Phase 5D Scope

### Deliverables

1. `app/templates/settings.html` — Settings page with credential management
2. `app/routers/settings.py` — Settings API endpoints
3. `app/services/credential_manager.py` — Fernet encryption for credentials
4. `app/models/credential.py` — Credential storage model (optional, can use .env)
5. Update `app/routers/views.py` — Settings page route
6. Update `app/main.py` — Register settings router

### Features to Implement

- View/update Anthropic API key (masked display)
- View/update Notion token and page ID
- View/update Slack webhook URL
- Test connection buttons for each service
- Timezone configuration
- Schedule configuration (day/time for weekly runs)
- Save settings to .env or database

---

## Implementation Details

### 1. `app/services/credential_manager.py`

```python
"""Credential encryption and management service."""
import os
from cryptography.fernet import Fernet
from app.config import settings

class CredentialManager:
    """Manages encrypted credential storage."""
    
    def __init__(self):
        # Use SECRET_KEY from settings or generate one
        key = settings.secret_key.encode() if settings.secret_key else Fernet.generate_key()
        # Fernet requires a 32-byte base64-encoded key
        # For simplicity, we'll hash the secret key to get correct format
        import hashlib
        import base64
        hashed = hashlib.sha256(key).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(hashed))
    
    def encrypt(self, value: str) -> str:
        """Encrypt a string value."""
        return self.fernet.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt an encrypted string."""
        return self.fernet.decrypt(encrypted.encode()).decode()
    
    def mask(self, value: str, visible_chars: int = 4) -> str:
        """Mask a value, showing only last N characters."""
        if not value or len(value) <= visible_chars:
            return "****"
        return "*" * (len(value) - visible_chars) + value[-visible_chars:]


credential_manager = CredentialManager()
```

### 2. `app/routers/settings.py`

```python
"""Settings and credential management endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import anthropic
from notion_client import Client as NotionClient

from app.config import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    """Current settings with masked credentials."""
    anthropic_key_set: bool
    anthropic_key_masked: str
    notion_token_set: bool
    notion_token_masked: str
    notion_page_id: Optional[str]
    slack_webhook_set: bool
    slack_webhook_masked: str
    timezone: str
    schedule_day: str
    schedule_time: str


class TestConnectionResult(BaseModel):
    """Result of connection test."""
    service: str
    success: bool
    message: str


@router.get("/", response_model=SettingsResponse)
async def get_settings():
    """Get current settings with masked credentials."""
    def mask(value: str, visible: int = 4) -> str:
        if not value:
            return ""
        return "*" * max(0, len(value) - visible) + value[-visible:] if len(value) > visible else "****"
    
    return SettingsResponse(
        anthropic_key_set=bool(settings.anthropic_api_key),
        anthropic_key_masked=mask(settings.anthropic_api_key or ""),
        notion_token_set=bool(settings.notion_token),
        notion_token_masked=mask(settings.notion_token or ""),
        notion_page_id=settings.notion_page_id,
        slack_webhook_set=bool(settings.slack_webhook_url),
        slack_webhook_masked=mask(settings.slack_webhook_url or "", 10),
        timezone=settings.timezone or "UTC",
        schedule_day="Sunday",  # TODO: Make configurable
        schedule_time="06:00",  # TODO: Make configurable
    )


@router.post("/test/anthropic", response_model=TestConnectionResult)
async def test_anthropic():
    """Test Anthropic API connection."""
    if not settings.anthropic_api_key:
        return TestConnectionResult(
            service="anthropic",
            success=False,
            message="API key not configured"
        )
    
    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        # Simple test - just verify the key format is valid
        # A real test would make a minimal API call
        if settings.anthropic_api_key.startswith("sk-ant-"):
            return TestConnectionResult(
                service="anthropic",
                success=True,
                message="API key format valid"
            )
        else:
            return TestConnectionResult(
                service="anthropic",
                success=False,
                message="Invalid API key format"
            )
    except Exception as e:
        return TestConnectionResult(
            service="anthropic",
            success=False,
            message=str(e)
        )


@router.post("/test/notion", response_model=TestConnectionResult)
async def test_notion():
    """Test Notion API connection."""
    if not settings.notion_token:
        return TestConnectionResult(
            service="notion",
            success=False,
            message="Token not configured"
        )
    
    try:
        notion = NotionClient(auth=settings.notion_token)
        # Try to get user info to verify token
        notion.users.me()
        return TestConnectionResult(
            service="notion",
            success=True,
            message="Connected successfully"
        )
    except Exception as e:
        return TestConnectionResult(
            service="notion",
            success=False,
            message=str(e)
        )


@router.post("/test/slack", response_model=TestConnectionResult)
async def test_slack():
    """Test Slack webhook connection."""
    if not settings.slack_webhook_url:
        return TestConnectionResult(
            service="slack",
            success=False,
            message="Webhook URL not configured"
        )
    
    try:
        # Validate URL format
        if not settings.slack_webhook_url.startswith("https://hooks.slack.com/"):
            return TestConnectionResult(
                service="slack",
                success=False,
                message="Invalid webhook URL format"
            )
        
        # Send a test message (commented out to avoid spam)
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         settings.slack_webhook_url,
        #         json={"text": "🔧 Weekly AI Sigint connection test"}
        #     )
        #     if response.status_code == 200:
        #         return TestConnectionResult(service="slack", success=True, message="Test message sent")
        
        return TestConnectionResult(
            service="slack",
            success=True,
            message="Webhook URL format valid"
        )
    except Exception as e:
        return TestConnectionResult(
            service="slack",
            success=False,
            message=str(e)
        )
```

### 3. `app/templates/settings.html`

Create a settings page with:
- Cards for each service (Anthropic, Notion, Slack)
- Masked credential display
- Test connection buttons
- Status indicators (green/red)
- Timezone selector
- Schedule configuration
- Instructions for updating credentials via .env file

Key UI elements:
```html
{% extends "base.html" %}
{% block title %}Settings - Weekly AI Sigint{% endblock %}
{% block content %}
<h1 class="text-2xl font-bold mb-6">Settings</h1>

<!-- API Credentials Section -->
<div class="bg-white rounded-lg shadow p-6 mb-6">
    <h2 class="text-lg font-semibold mb-4">API Credentials</h2>
    <p class="text-gray-600 text-sm mb-4">
        Credentials are stored in the <code class="bg-gray-100 px-1 rounded">.env</code> file. 
        Update the file directly and restart the server to apply changes.
    </p>
    
    <!-- Anthropic Card -->
    <div class="border rounded-lg p-4 mb-4">
        <div class="flex justify-between items-center">
            <div>
                <h3 class="font-medium">Anthropic API</h3>
                <p class="text-sm text-gray-500" id="anthropic-status">Loading...</p>
            </div>
            <button onclick="testConnection('anthropic')" class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">
                Test Connection
            </button>
        </div>
    </div>
    
    <!-- Similar cards for Notion and Slack -->
</div>

<!-- Schedule Section -->
<div class="bg-white rounded-lg shadow p-6">
    <h2 class="text-lg font-semibold mb-4">Schedule</h2>
    <!-- Timezone selector, day/time pickers -->
</div>

<script>
async function testConnection(service) {
    const statusEl = document.getElementById(`${service}-status`);
    statusEl.textContent = 'Testing...';
    try {
        const response = await fetch(`/api/settings/test/${service}`, { method: 'POST' });
        const data = await response.json();
        statusEl.textContent = data.success ? `✅ ${data.message}` : `❌ ${data.message}`;
        statusEl.className = data.success ? 'text-sm text-green-600' : 'text-sm text-red-600';
    } catch (error) {
        statusEl.textContent = `❌ Error: ${error.message}`;
        statusEl.className = 'text-sm text-red-600';
    }
}

// Load settings on page load
async function loadSettings() {
    const response = await fetch('/api/settings/');
    const data = await response.json();
    // Update UI with masked values and status
}
loadSettings();
</script>
{% endblock %}
```

### 4. Update `app/routers/views.py`

```python
@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page."""
    return templates.TemplateResponse("settings.html", {
        "request": request,
    })
```

### 5. Update `app/main.py`

```python
from app.routers import sources, content, manual, briefings, views, settings

# Register settings router
app.include_router(settings.router)
```

---

## Verification Gate

After implementation, verify:

```bash
# 1. Start server
source venv/bin/activate
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
uvicorn app.main:app --reload --port 8000 &
sleep 3

# 2. Check health
curl -s http://localhost:8000/health

# 3. Check settings page renders
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/settings
# Expected: 200

# 4. Check settings API (single line!)
curl -s http://localhost:8000/api/settings/ | python3 -m json.tool

# 5. Test connection endpoints (single line each!)
curl -s -X POST http://localhost:8000/api/settings/test/anthropic | python3 -m json.tool
curl -s -X POST http://localhost:8000/api/settings/test/notion | python3 -m json.tool
curl -s -X POST http://localhost:8000/api/settings/test/slack | python3 -m json.tool

# 6. Check for errors
cat /tmp/phase5d-test.log | grep -i "error\|exception" | head -5

# 7. Open in browser
echo "Open http://localhost:8000/settings in browser to verify UI"
```

**Success criteria:**
- [ ] Settings page renders with navigation
- [ ] GET /api/settings/ returns masked credentials
- [ ] Test connection buttons work
- [ ] No server errors in console
- [ ] Credentials are properly masked (not exposed)

---

## Security Considerations

**CRITICAL**: Never expose full credentials in API responses or logs.

1. Always mask credentials before returning them
2. Use Fernet encryption if storing credentials in database
3. Validate credential format before testing connections
4. Don't log credential values
5. Test connection endpoints should use minimal API calls

---

## Commit After Verification

```bash
git add -A
git commit -m "Phase 5D complete: Settings and credentials UI"
```

---

## Next Phase

After 5D is verified, proceed to **Phase 5E: Prompt Editor** or **Phase 5F: APScheduler Integration**.
