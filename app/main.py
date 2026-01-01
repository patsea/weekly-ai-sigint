"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.models.database import init_db
from app.routers import sources, content, manual, briefings, views, settings, prompt, scheduler
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    print("🚀 Starting Weekly AI Sigint...")
    await init_db()
    print("✅ Database initialized")
    start_scheduler()
    print("✅ Scheduler started")

    yield

    # Shutdown
    print("👋 Shutting down...")
    stop_scheduler()


app = FastAPI(
    title="Weekly AI Sigint",
    description="AI/enterprise tech content aggregator and synthesizer",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Register routers
app.include_router(views.router)  # HTML views (must be before API routers to handle "/")
app.include_router(sources.router)
app.include_router(content.router)
app.include_router(briefings.router)
app.include_router(manual.router)
app.include_router(settings.router)
app.include_router(prompt.router)
app.include_router(scheduler.router)


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
