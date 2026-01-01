"""API routes for manually triggering pipeline operations."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.models.database import get_session
from app.services.fetcher import fetch_from_all_sources
from app.services.synthesizer import synthesize_weekly_briefing
from app.services.notion_export import export_briefing_to_notion, NotionExportError
from app.services.slack_notify import send_briefing_to_slack, SlackNotifyError

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


class NotionExportResult(BaseModel):
    """Schema for Notion export result."""
    success: bool
    briefing_id: int
    notion_page_id: str
    notion_url: str


@router.post("/export/notion", response_model=NotionExportResult)
async def run_notion_export(
    briefing_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Manually trigger Notion export.

    Args:
        briefing_id: ID of briefing to export (None = latest)
        session: Database session

    Returns:
        Export result with Notion page details

    Raises:
        400: If no briefing found or Notion not configured
        500: If export fails
    """
    try:
        result = await export_briefing_to_notion(session, briefing_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotionExportError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notion export failed: {str(e)}")


class SlackNotifyResult(BaseModel):
    """Schema for Slack notification result."""
    success: bool
    briefing_id: int
    message: str


@router.post("/notify/slack", response_model=SlackNotifyResult)
async def run_slack_notify(
    briefing_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Manually trigger Slack notification.

    Args:
        briefing_id: ID of briefing to notify about (None = latest)
        session: Database session

    Returns:
        Notification result

    Raises:
        400: If no briefing found or Slack not configured
        500: If notification fails
    """
    try:
        result = await send_briefing_to_slack(session, briefing_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SlackNotifyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Slack notification failed: {str(e)}")


class PipelineResult(BaseModel):
    """Schema for full pipeline result."""
    success: bool
    fetch_result: FetchResult
    synthesize_result: SynthesizeResult
    notion_result: Optional[NotionExportResult] = None
    slack_result: Optional[SlackNotifyResult] = None
    errors: List[str]


@router.post("/full-pipeline", response_model=PipelineResult)
async def run_full_pipeline(
    days_back: int = 7,
    export_notion: bool = True,
    notify_slack: bool = True,
    session: AsyncSession = Depends(get_session)
):
    """
    Run the complete pipeline: fetch → synthesize → export → notify.

    Args:
        days_back: Number of days of content to synthesize (default: 7)
        export_notion: Whether to export to Notion (default: True)
        notify_slack: Whether to send Slack notification (default: True)
        session: Database session

    Returns:
        Combined results from all pipeline stages

    Note:
        The pipeline continues even if optional steps (Notion/Slack) fail.
        Check the 'errors' field for any issues encountered.
    """
    errors = []

    # Step 1: Fetch content
    try:
        fetch_results = await fetch_from_all_sources(session)
        total_fetched = sum(r["fetched"] for r in fetch_results)
        total_new = sum(r["new"] for r in fetch_results)
        total_duplicates = sum(r["duplicates"] for r in fetch_results)

        fetch_result = FetchResult(
            total_sources=len(fetch_results),
            total_fetched=total_fetched,
            total_new=total_new,
            total_duplicates=total_duplicates,
            sources=fetch_results
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fetch step failed: {str(e)}"
        )

    # Step 2: Synthesize briefing
    try:
        briefing = await synthesize_weekly_briefing(session, days_back=days_back)

        synthesize_result = SynthesizeResult(
            briefing_id=briefing.id,
            title=briefing.title,
            content_items_processed=len(briefing.content_items),
            status="completed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Synthesize step failed: {str(e)}"
        )

    # Step 3: Export to Notion (optional)
    notion_result = None
    if export_notion:
        try:
            notion_result = NotionExportResult(
                **await export_briefing_to_notion(session, briefing.id)
            )
        except Exception as e:
            errors.append(f"Notion export failed: {str(e)}")

    # Step 4: Send Slack notification (optional)
    slack_result = None
    if notify_slack:
        try:
            slack_result = SlackNotifyResult(
                **await send_briefing_to_slack(session, briefing.id)
            )
        except Exception as e:
            errors.append(f"Slack notification failed: {str(e)}")

    return PipelineResult(
        success=True,
        fetch_result=fetch_result,
        synthesize_result=synthesize_result,
        notion_result=notion_result,
        slack_result=slack_result,
        errors=errors
    )
