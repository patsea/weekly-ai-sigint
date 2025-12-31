"""API routes for manually triggering pipeline operations."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any

from app.models.database import get_session
from app.services.fetcher import fetch_from_all_sources
from app.services.synthesizer import synthesize_weekly_briefing

router = APIRouter(prefix="/api/run", tags=["manual"])


class FetchResult(BaseModel):
    """Schema for fetch result."""
    total_sources: int
    total_fetched: int
    total_new: int
    total_duplicates: int
    sources: List[Dict[str, Any]]


@router.post("/fetch", response_model=FetchResult)
async def run_fetch(session: AsyncSession = Depends(get_session)):
    """
    Manually trigger content fetch from all active sources.

    This fetches content from all active sources and saves new items
    to the database. Duplicate URLs are automatically skipped.
    """
    results = await fetch_from_all_sources(session)

    # Calculate totals
    total_fetched = sum(r["fetched"] for r in results)
    total_new = sum(r["new"] for r in results)
    total_duplicates = sum(r["duplicates"] for r in results)

    return {
        "total_sources": len(results),
        "total_fetched": total_fetched,
        "total_new": total_new,
        "total_duplicates": total_duplicates,
        "sources": results
    }


class SynthesizeResult(BaseModel):
    """Schema for synthesize result."""
    briefing_id: int
    title: str
    content_items_processed: int
    status: str


@router.post("/synthesize", response_model=SynthesizeResult)
async def run_synthesize(
    days_back: int = 7, session: AsyncSession = Depends(get_session)
):
    """
    Manually trigger briefing synthesis with Claude.

    Args:
        days_back: Number of days of content to synthesize (default: 7)
        session: Database session

    Returns:
        Synthesis result with briefing ID and metadata

    Raises:
        400: If no content available to synthesize
        500: If synthesis fails
    """
    try:
        briefing = await synthesize_weekly_briefing(session, days_back=days_back)

        return {
            "briefing_id": briefing.id,
            "title": briefing.title,
            "content_items_processed": len(briefing.content_items),
            "status": "completed",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.post("/export/notion")
async def run_notion_export():
    """
    Manually trigger Notion export.

    (To be implemented in Phase 4)
    """
    return {
        "status": "not_implemented",
        "message": "Notion export will be implemented in Phase 4"
    }


@router.post("/notify/slack")
async def run_slack_notify():
    """
    Manually trigger Slack notification.

    (To be implemented in Phase 4)
    """
    return {
        "status": "not_implemented",
        "message": "Slack notifications will be implemented in Phase 4"
    }


@router.post("/full-pipeline")
async def run_full_pipeline():
    """
    Run the complete pipeline: fetch → synthesize → export → notify.

    (To be fully implemented across all phases)
    """
    return {
        "status": "partial",
        "message": "Only fetch is available in Phase 2. Full pipeline will be completed in later phases."
    }
