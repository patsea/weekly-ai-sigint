# Weekly AI Sigint — Phase 5A Instructions

> Execute Phase 5A: Base Templates + Dashboard

## Pre-Flight

```bash
# Verify working directory
pwd  # Should be weekly-ai-sigint

# Verify Phase 4 complete
ls -la app/services/notion_export.py app/services/slack_notify.py

# Verify server can start
source venv/bin/activate
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
```

---

## Phase 5A Scope

### Deliverables

1. `app/templates/base.html` — Tailwind CSS layout with navigation
2. `app/templates/index.html` — Dashboard with system stats
3. `app/static/css/custom.css` — Custom styles (minimal)
4. `app/routers/views.py` — HTML page routes
5. Update `app/main.py` — Mount templates and static files

### DO NOT Implement Yet

- Sources management UI (Phase 5B)
- Briefings viewer (Phase 5C)
- Settings page (Phase 5D)
- Prompt editor (Phase 5E)
- Scheduler (Phase 5F)

---

## Implementation Details

### 1. `app/templates/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Weekly AI Sigint{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="/static/css/custom.css">
</head>
<body class="bg-gray-100 min-h-screen">
    <nav class="bg-white shadow">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <span class="text-xl font-bold">📡 Weekly AI Sigint</span>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/" class="text-gray-700 hover:text-blue-600 {% if request.url.path == '/' %}font-semibold text-blue-600{% endif %}">Dashboard</a>
                    <a href="/sources" class="text-gray-700 hover:text-blue-600 {% if '/sources' in request.url.path %}font-semibold text-blue-600{% endif %}">Sources</a>
                    <a href="/briefings" class="text-gray-700 hover:text-blue-600 {% if '/briefings' in request.url.path %}font-semibold text-blue-600{% endif %}">Briefings</a>
                    <a href="/settings" class="text-gray-700 hover:text-blue-600 {% if '/settings' in request.url.path %}font-semibold text-blue-600{% endif %}">Settings</a>
                </div>
            </div>
        </div>
    </nav>
    <main class="max-w-7xl mx-auto py-6 px-4">
        {% block content %}{% endblock %}
    </main>
    <footer class="max-w-7xl mx-auto py-4 px-4 text-center text-gray-500 text-sm">
        Weekly AI Sigint v1.0
    </footer>
</body>
</html>
```

### 2. `app/templates/index.html`

Dashboard should display:
- **Stats Cards**: Total sources, Active sources, Content items (last 7 days), Briefings generated
- **Last Briefing**: Title, date, link to view
- **Next Scheduled Run**: Date/time (placeholder until 5F)
- **Quick Actions**: Buttons for Fetch, Synthesize, Full Pipeline

Use Tailwind grid for layout:
```html
{% extends "base.html" %}
{% block title %}Dashboard - Weekly AI Sigint{% endblock %}
{% block content %}
<h1 class="text-2xl font-bold mb-6">Dashboard</h1>

<!-- Stats Grid -->
<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
    <!-- Card for each stat -->
</div>

<!-- Last Briefing -->
<div class="bg-white rounded-lg shadow p-6 mb-8">
    <h2 class="text-lg font-semibold mb-4">Latest Briefing</h2>
    <!-- Briefing details or "No briefings yet" -->
</div>

<!-- Quick Actions -->
<div class="bg-white rounded-lg shadow p-6">
    <h2 class="text-lg font-semibold mb-4">Quick Actions</h2>
    <div class="flex space-x-4">
        <button onclick="runAction('fetch')" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
            Fetch Content
        </button>
        <button onclick="runAction('synthesize')" class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
            Synthesize Briefing
        </button>
        <button onclick="runAction('full-pipeline')" class="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600">
            Run Full Pipeline
        </button>
    </div>
    <div id="action-status" class="mt-4 text-sm text-gray-600"></div>
</div>

<script>
async function runAction(action) {
    const statusEl = document.getElementById('action-status');
    statusEl.textContent = `Running ${action}...`;
    try {
        const response = await fetch(`/api/run/${action}`, { method: 'POST' });
        const data = await response.json();
        statusEl.textContent = response.ok 
            ? `✅ ${action} completed successfully` 
            : `❌ Error: ${data.detail || 'Unknown error'}`;
    } catch (error) {
        statusEl.textContent = `❌ Error: ${error.message}`;
    }
}
</script>
{% endblock %}
```

### 3. `app/routers/views.py`

```python
"""HTML view routes (separate from API routes)."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.models.database import get_session
from app.models.source import Source
from app.models.content import ContentItem
from app.models.briefing import Briefing

router = APIRouter(tags=["views"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, session: AsyncSession = Depends(get_session)):
    """Render dashboard page with system stats."""
    # Get counts
    total_sources = await session.scalar(select(func.count(Source.id)))
    active_sources = await session.scalar(
        select(func.count(Source.id)).where(Source.is_active == True)
    )
    
    # Content items in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_content = await session.scalar(
        select(func.count(ContentItem.id)).where(ContentItem.fetched_at >= week_ago)
    )
    
    # Total briefings
    total_briefings = await session.scalar(select(func.count(Briefing.id)))
    
    # Latest briefing
    latest_briefing = await session.scalar(
        select(Briefing).order_by(Briefing.created_at.desc()).limit(1)
    )
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": {
            "total_sources": total_sources or 0,
            "active_sources": active_sources or 0,
            "recent_content": recent_content or 0,
            "total_briefings": total_briefings or 0,
        },
        "latest_briefing": latest_briefing,
        "next_run": None,  # Placeholder until Phase 5F
    })


# Placeholder routes for other pages (will be implemented in later sub-phases)
@router.get("/sources", response_class=HTMLResponse)
async def sources_page(request: Request):
    """Sources management page (placeholder)."""
    return templates.TemplateResponse("base.html", {
        "request": request,
    })


@router.get("/briefings", response_class=HTMLResponse)
async def briefings_page(request: Request):
    """Briefings list page (placeholder)."""
    return templates.TemplateResponse("base.html", {
        "request": request,
    })


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page (placeholder)."""
    return templates.TemplateResponse("base.html", {
        "request": request,
    })
```

### 4. `app/static/css/custom.css`

```css
/* Custom styles for Weekly AI Sigint */

/* Loading spinner */
.spinner {
    border: 2px solid #f3f3f3;
    border-top: 2px solid #3498db;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    animation: spin 1s linear infinite;
    display: inline-block;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Status badges */
.badge-active {
    background-color: #10b981;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 9999px;
    font-size: 0.75rem;
}

.badge-inactive {
    background-color: #6b7280;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 9999px;
    font-size: 0.75rem;
}
```

### 5. Update `app/main.py`

Add these imports and configurations:
```python
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import views

# After app creation, add:
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Register views router (for HTML pages)
app.include_router(views.router)
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

# 3. Check dashboard renders
curl -s http://localhost:8000/ | grep -i "dashboard\|Weekly AI Sigint"

# 4. Check static files
curl -s http://localhost:8000/static/css/custom.css | head -5

# 5. Check templates directory exists
ls -la app/templates/

# 6. Open in browser
echo "Open http://localhost:8000 in browser to verify visually"
```

**Success criteria:**
- [ ] Homepage renders with navigation
- [ ] Dashboard shows stats (may be zeros)
- [ ] Quick action buttons visible
- [ ] No server errors in console
- [ ] Static CSS loads

---

## Commit After Verification

```bash
git add -A
git commit -m "Phase 5A complete: Base templates and dashboard"
```

---

## Next Phase

After 5A is verified, proceed to **Phase 5B: Sources Management UI**.
