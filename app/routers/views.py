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
        select(func.count(Source.id)).where(Source.active == True)
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


# Sources management page
@router.get("/sources", response_class=HTMLResponse)
async def sources_page(request: Request):
    """Sources management page."""
    return templates.TemplateResponse("sources.html", {
        "request": request,
    })


@router.get("/briefings", response_class=HTMLResponse)
async def briefings_page(request: Request):
    """Briefings list page."""
    return templates.TemplateResponse("briefings.html", {
        "request": request,
    })


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page."""
    return templates.TemplateResponse("settings.html", {
        "request": request,
    })
