# Weekly AI Sigint — Phase 5F Instructions

> Execute Phase 5F: APScheduler Integration

## Pre-Flight

```bash
# Verify working directory
pwd  # Should be weekly-ai-sigint

# Read best practices first
cat ~/Dropbox/ALOMA/claude-code/CLAUDE_CODE_UNIVERSAL_BEST_PRACTICES.md | head -100

# Verify Phase 5E complete
ls -la app/templates/prompt.html app/routers/prompt.py

# Check if apscheduler is installed
source venv/bin/activate
pip show apscheduler || pip install apscheduler --break-system-packages

# Kill any existing server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
```

---

## Phase 5F Scope

### Deliverables

1. `app/services/scheduler.py` — APScheduler service with weekly cron job
2. `app/routers/scheduler.py` — Scheduler status and control API endpoints
3. Update `app/main.py` — Start scheduler in lifespan context
4. Update `app/templates/index.html` — Show next scheduled run on dashboard
5. Update `app/config.py` — Add scheduler configuration options

### Features to Implement

- Weekly scheduled job (configurable day/time)
- Full pipeline execution (fetch → synthesize → export → notify)
- Scheduler status endpoint (next run, last run, job state)
- Manual pause/resume controls
- Job history tracking
- Dashboard integration showing next run

---

## Implementation Details

### 1. `app/services/scheduler.py`

```python
"""APScheduler service for weekly briefing automation."""
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from app.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None

# Job execution history (in-memory, resets on restart)
job_history: list[dict] = []


async def run_weekly_pipeline():
    """Execute the full weekly briefing pipeline.
    
    Pipeline steps:
    1. Fetch content from all active sources
    2. Synthesize briefing with Claude
    3. Export to Notion (if configured)
    4. Send Slack notification (if configured)
    """
    from app.models.database import async_session
    from app.services.fetcher import fetch_all_sources
    from app.services.synthesizer import synthesize_briefing
    from app.services.notion_export import export_briefing_to_notion
    from app.services.slack_notify import send_slack_notification
    
    start_time = datetime.now()
    result = {
        "started_at": start_time.isoformat(),
        "steps": {},
        "success": False,
        "error": None,
    }
    
    try:
        async with async_session() as session:
            # Step 1: Fetch content
            logger.info("Pipeline Step 1: Fetching content from sources...")
            fetch_result = await fetch_all_sources(session)
            result["steps"]["fetch"] = {
                "success": True,
                "items_fetched": fetch_result.get("total_items", 0),
            }
            
            # Step 2: Synthesize briefing
            logger.info("Pipeline Step 2: Synthesizing briefing with Claude...")
            briefing = await synthesize_briefing(session, days_back=7)
            result["steps"]["synthesize"] = {
                "success": True,
                "briefing_id": briefing.id if briefing else None,
            }
            
            if not briefing:
                raise Exception("No briefing generated")
            
            # Step 3: Export to Notion (if configured)
            if settings.notion_token and settings.notion_page_id:
                logger.info("Pipeline Step 3: Exporting to Notion...")
                try:
                    notion_result = await export_briefing_to_notion(session, briefing.id)
                    result["steps"]["notion"] = {
                        "success": True,
                        "page_url": notion_result.get("notion_url"),
                    }
                except Exception as e:
                    logger.warning(f"Notion export failed: {e}")
                    result["steps"]["notion"] = {"success": False, "error": str(e)}
            else:
                result["steps"]["notion"] = {"success": False, "error": "Not configured"}
            
            # Step 4: Send Slack notification (if configured)
            if settings.slack_webhook_url:
                logger.info("Pipeline Step 4: Sending Slack notification...")
                try:
                    slack_result = await send_slack_notification(session, briefing.id)
                    result["steps"]["slack"] = {
                        "success": True,
                    }
                except Exception as e:
                    logger.warning(f"Slack notification failed: {e}")
                    result["steps"]["slack"] = {"success": False, "error": str(e)}
            else:
                result["steps"]["slack"] = {"success": False, "error": "Not configured"}
            
            result["success"] = True
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        result["error"] = str(e)
    
    result["completed_at"] = datetime.now().isoformat()
    result["duration_seconds"] = (datetime.now() - start_time).total_seconds()
    
    # Store in history (keep last 10)
    job_history.insert(0, result)
    if len(job_history) > 10:
        job_history.pop()
    
    logger.info(f"Pipeline completed: success={result['success']}")
    return result


def job_listener(event):
    """Listen for job execution events."""
    if event.exception:
        logger.error(f"Scheduled job failed: {event.exception}")
    else:
        logger.info(f"Scheduled job completed successfully")


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Get the global scheduler instance."""
    return scheduler


def init_scheduler() -> AsyncIOScheduler:
    """Initialize the APScheduler instance."""
    global scheduler
    
    if scheduler is not None:
        return scheduler
    
    scheduler = AsyncIOScheduler()
    
    # Add job listener for logging
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    # Get schedule from settings
    day_of_week = getattr(settings, 'weekly_run_day', 'sun')  # Default: Sunday
    hour = getattr(settings, 'weekly_run_hour', 6)  # Default: 6 AM
    minute = getattr(settings, 'weekly_run_minute', 0)  # Default: 0
    timezone = getattr(settings, 'timezone', 'UTC')
    
    # Add the weekly job
    scheduler.add_job(
        run_weekly_pipeline,
        CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=timezone,
        ),
        id='weekly_briefing',
        name='Weekly AI Sigint Briefing',
        replace_existing=True,
    )
    
    logger.info(f"Scheduler initialized: {day_of_week} at {hour:02d}:{minute:02d} {timezone}")
    return scheduler


def start_scheduler():
    """Start the scheduler."""
    global scheduler
    if scheduler is None:
        scheduler = init_scheduler()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler():
    """Stop the scheduler."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def pause_scheduler():
    """Pause the scheduler (jobs won't run but scheduler stays active)."""
    global scheduler
    if scheduler:
        scheduler.pause()
        logger.info("Scheduler paused")


def resume_scheduler():
    """Resume the scheduler."""
    global scheduler
    if scheduler:
        scheduler.resume()
        logger.info("Scheduler resumed")


def get_scheduler_status() -> dict:
    """Get current scheduler status."""
    global scheduler, job_history
    
    if scheduler is None:
        return {
            "running": False,
            "paused": False,
            "next_run": None,
            "last_run": None,
            "job_count": 0,
        }
    
    job = scheduler.get_job('weekly_briefing')
    next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
    
    return {
        "running": scheduler.running,
        "paused": scheduler.state == 2,  # STATE_PAUSED = 2
        "next_run": next_run,
        "last_run": job_history[0] if job_history else None,
        "job_count": len(scheduler.get_jobs()),
        "history": job_history[:5],  # Last 5 runs
    }
```

### 2. `app/routers/scheduler.py`

```python
"""API routes for scheduler management."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.services.scheduler import (
    get_scheduler_status,
    pause_scheduler,
    resume_scheduler,
    run_weekly_pipeline,
    job_history,
)

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


class SchedulerStatus(BaseModel):
    """Scheduler status response."""
    running: bool
    paused: bool
    next_run: Optional[str]
    last_run: Optional[dict]
    job_count: int
    history: List[dict]


class ActionResult(BaseModel):
    """Result of scheduler action."""
    success: bool
    message: str
    status: Optional[dict] = None


@router.get("/status", response_model=SchedulerStatus)
async def get_status():
    """Get scheduler status including next run time and history."""
    return get_scheduler_status()


@router.post("/pause", response_model=ActionResult)
async def pause():
    """Pause the scheduler (jobs won't execute)."""
    try:
        pause_scheduler()
        return ActionResult(
            success=True,
            message="Scheduler paused",
            status=get_scheduler_status(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume", response_model=ActionResult)
async def resume():
    """Resume the scheduler."""
    try:
        resume_scheduler()
        return ActionResult(
            success=True,
            message="Scheduler resumed",
            status=get_scheduler_status(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-now", response_model=ActionResult)
async def run_now():
    """Manually trigger the weekly pipeline immediately."""
    try:
        result = await run_weekly_pipeline()
        return ActionResult(
            success=result.get("success", False),
            message="Pipeline executed" if result.get("success") else f"Pipeline failed: {result.get('error')}",
            status=get_scheduler_status(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history():
    """Get job execution history."""
    return {
        "history": job_history,
        "count": len(job_history),
    }
```

### 3. Update `app/config.py`

Add scheduler configuration options:

```python
# Add these fields to the Settings class
weekly_run_day: str = "sun"  # Day of week: mon, tue, wed, thu, fri, sat, sun
weekly_run_hour: int = 6     # Hour (0-23)
weekly_run_minute: int = 0   # Minute (0-59)
timezone: str = "UTC"        # Timezone for scheduling
```

### 4. Update `app/main.py`

```python
"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.models.database import init_db
from app.routers import sources, content, manual, briefings, views, settings, prompt, scheduler
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    await init_db()
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


app = FastAPI(
    title="Weekly AI Sigint",
    description="AI-powered weekly intelligence briefing system",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Register routers
app.include_router(views.router)
app.include_router(sources.router)
app.include_router(content.router)
app.include_router(briefings.router)
app.include_router(manual.router)
app.include_router(settings.router)
app.include_router(prompt.router)
app.include_router(scheduler.router)  # Add scheduler router


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.services.scheduler import get_scheduler_status
    sched_status = get_scheduler_status()
    return {
        "status": "healthy",
        "service": "weekly-ai-sigint",
        "version": "1.0.0",
        "scheduler": {
            "running": sched_status.get("running", False),
            "next_run": sched_status.get("next_run"),
        }
    }
```

### 5. Update `app/templates/index.html`

Add scheduler status section to the dashboard. Find the "Next Scheduled Run" placeholder and update:

```html
<!-- Next Scheduled Run Card -->
<div class="bg-white rounded-lg shadow p-6">
    <h2 class="text-lg font-semibold mb-4">Scheduler Status</h2>
    <div id="scheduler-status">
        <div class="flex items-center mb-2">
            <span class="w-3 h-3 rounded-full mr-2" id="scheduler-indicator"></span>
            <span id="scheduler-state">Loading...</span>
        </div>
        <p class="text-sm text-gray-500">Next run:</p>
        <p class="text-lg font-medium" id="next-run">--</p>
        <div class="mt-4 flex gap-2">
            <button onclick="toggleScheduler()" id="toggle-btn" class="text-sm bg-gray-200 px-3 py-1 rounded hover:bg-gray-300">
                Pause
            </button>
            <button onclick="runNow()" class="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">
                Run Now
            </button>
        </div>
    </div>
</div>

<script>
async function loadSchedulerStatus() {
    try {
        const response = await fetch('/api/scheduler/status');
        const data = await response.json();
        
        const indicator = document.getElementById('scheduler-indicator');
        const state = document.getElementById('scheduler-state');
        const nextRun = document.getElementById('next-run');
        const toggleBtn = document.getElementById('toggle-btn');
        
        if (data.running && !data.paused) {
            indicator.className = 'w-3 h-3 rounded-full mr-2 bg-green-500';
            state.textContent = 'Running';
            toggleBtn.textContent = 'Pause';
        } else if (data.paused) {
            indicator.className = 'w-3 h-3 rounded-full mr-2 bg-yellow-500';
            state.textContent = 'Paused';
            toggleBtn.textContent = 'Resume';
        } else {
            indicator.className = 'w-3 h-3 rounded-full mr-2 bg-red-500';
            state.textContent = 'Stopped';
            toggleBtn.textContent = 'Start';
        }
        
        if (data.next_run) {
            const nextDate = new Date(data.next_run);
            nextRun.textContent = nextDate.toLocaleString();
        } else {
            nextRun.textContent = 'Not scheduled';
        }
    } catch (error) {
        console.error('Failed to load scheduler status:', error);
    }
}

async function toggleScheduler() {
    const btn = document.getElementById('toggle-btn');
    const action = btn.textContent.toLowerCase();
    
    try {
        const response = await fetch(`/api/scheduler/${action}`, { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            loadSchedulerStatus();
        }
    } catch (error) {
        console.error('Failed to toggle scheduler:', error);
    }
}

async function runNow() {
    if (!confirm('Run the full pipeline now? This may take a few minutes.')) return;
    
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Running...';
    
    try {
        const response = await fetch('/api/scheduler/run-now', { method: 'POST' });
        const data = await response.json();
        alert(data.message);
        loadSchedulerStatus();
    } catch (error) {
        alert('Pipeline failed: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Run Now';
    }
}

// Load on page load
loadSchedulerStatus();
// Refresh every 30 seconds
setInterval(loadSchedulerStatus, 30000);
</script>
```

### 6. Update `.env.example`

Add scheduler configuration:

```bash
# Scheduler Configuration
WEEKLY_RUN_DAY=sun       # Day: mon, tue, wed, thu, fri, sat, sun
WEEKLY_RUN_HOUR=6        # Hour: 0-23
WEEKLY_RUN_MINUTE=0      # Minute: 0-59
TIMEZONE=UTC             # Timezone for scheduling
```

---

## Verification Gate

After implementation, verify:

```bash
# 1. Ensure apscheduler is installed
source venv/bin/activate
pip show apscheduler || pip install apscheduler --break-system-packages

# 2. Start server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
uvicorn app.main:app --port 8000 > /tmp/phase5f-test.log 2>&1 &
sleep 3

# 3. Check health includes scheduler
curl -s http://localhost:8000/health | python3 -m json.tool

# 4. Check scheduler status endpoint (single line!)
curl -s http://localhost:8000/api/scheduler/status | python3 -m json.tool

# 5. Test pause endpoint
curl -s -X POST http://localhost:8000/api/scheduler/pause | python3 -m json.tool

# 6. Verify paused
curl -s http://localhost:8000/api/scheduler/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Paused: {d[\"paused\"]}')"

# 7. Test resume endpoint
curl -s -X POST http://localhost:8000/api/scheduler/resume | python3 -m json.tool

# 8. Check dashboard shows scheduler
curl -s http://localhost:8000/ | grep -c "Scheduler Status"
# Expected: >= 1

# 9. Check for startup errors
cat /tmp/phase5f-test.log | grep -i "error\|exception" | head -5

# 10. Check scheduler initialized in logs
cat /tmp/phase5f-test.log | grep -i "scheduler"

# 11. Get history endpoint
curl -s http://localhost:8000/api/scheduler/history | python3 -m json.tool

# 12. Stop server
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
```

**Success criteria:**
- [ ] Health endpoint includes scheduler status
- [ ] GET /api/scheduler/status returns next run time
- [ ] POST /api/scheduler/pause pauses jobs
- [ ] POST /api/scheduler/resume resumes jobs
- [ ] POST /api/scheduler/run-now triggers pipeline (may fail without API key)
- [ ] Dashboard shows scheduler status card
- [ ] Scheduler initializes on startup (check logs)
- [ ] No server errors

---

## Optional: Test Run-Now (Requires API Key)

If you have valid credentials configured:

```bash
# This will run the full pipeline
curl -s -X POST http://localhost:8000/api/scheduler/run-now | python3 -m json.tool

# Check history after run
curl -s http://localhost:8000/api/scheduler/history | python3 -m json.tool
```

---

## Commit After Verification

```bash
git add -A
git commit -m "Phase 5F complete: APScheduler integration

- Added scheduler.py service with AsyncIOScheduler
- Weekly cron job for full pipeline (fetch → synthesize → export → notify)
- Scheduler API: status, pause, resume, run-now, history
- Dashboard integration with live scheduler status
- Job execution history tracking (last 10 runs)
- Configurable schedule via .env (day, hour, minute, timezone)"
```

---

## Phase 5 Complete! 🎉

After Phase 5F is verified, the entire Phase 5 (UI & Scheduling) is complete:

| Sub-Phase | Feature | Status |
|-----------|---------|--------|
| 5A | Base Templates + Dashboard | ✅ |
| 5B | Sources Management UI | ✅ |
| 5C | Briefings Viewer | ✅ |
| 5D | Settings + Credentials UI | ✅ |
| 5E | Prompt Editor | ✅ |
| 5F | APScheduler Integration | ✅ |

The application is now fully functional with:
- Web UI for all management tasks
- Automated weekly scheduling
- Manual pipeline triggers
- Full observability (status, history, logs)
