"""API routes for manually triggering pipeline operations."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any

from app.models.database import get_session
from app.services.fetcher import fetch_from_all_sources

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


@router.post("/synthesize")
async def run_synthesize():
    """
    Manually trigger briefing synthesis with Claude.

    (To be implemented in Phase 3)
    """
    return {
        "status": "not_implemented",
        "message": "Synthesis will be implemented in Phase 3"
    }


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
