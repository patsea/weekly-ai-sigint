"""API routes for briefing management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.models.database import get_session
from app.models.briefing import Briefing

router = APIRouter(prefix="/api/briefings", tags=["briefings"])


class BriefingResponse(BaseModel):
    """Schema for briefing response."""

    id: int
    title: str
    content: str
    week_start: datetime
    week_end: datetime
    created_at: datetime
    notion_page_id: Optional[str]
    notion_exported_at: Optional[datetime]
    slack_sent_at: Optional[datetime]

    class Config:
        from_attributes = True


class BriefingListItem(BaseModel):
    """Schema for briefing list (without full content)."""

    id: int
    title: str
    week_start: datetime
    week_end: datetime
    created_at: datetime
    notion_page_id: Optional[str]
    notion_exported_at: Optional[datetime]
    slack_sent_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[BriefingListItem])
async def list_briefings(
    limit: int = 50, session: AsyncSession = Depends(get_session)
):
    """
    List all briefings (without full content).

    Args:
        limit: Maximum number of briefings to return
        session: Database session

    Returns:
        List of briefings ordered by creation date (newest first)
    """
    stmt = select(Briefing).order_by(Briefing.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    briefings = result.scalars().all()

    return briefings


@router.get("/latest", response_model=BriefingResponse)
async def get_latest_briefing(session: AsyncSession = Depends(get_session)):
    """
    Get the most recent briefing with full content.

    Returns:
        Latest briefing

    Raises:
        404: If no briefings exist
    """
    stmt = select(Briefing).order_by(Briefing.created_at.desc()).limit(1)
    result = await session.execute(stmt)
    briefing = result.scalar_one_or_none()

    if not briefing:
        raise HTTPException(status_code=404, detail="No briefings found")

    return briefing


@router.get("/{briefing_id}", response_model=BriefingResponse)
async def get_briefing(
    briefing_id: int, session: AsyncSession = Depends(get_session)
):
    """
    Get a specific briefing by ID.

    Args:
        briefing_id: ID of the briefing to retrieve
        session: Database session

    Returns:
        Briefing with full content

    Raises:
        404: If briefing not found
    """
    stmt = select(Briefing).where(Briefing.id == briefing_id)
    result = await session.execute(stmt)
    briefing = result.scalar_one_or_none()

    if not briefing:
        raise HTTPException(
            status_code=404, detail=f"Briefing {briefing_id} not found"
        )

    return briefing


@router.delete("/{briefing_id}")
async def delete_briefing(
    briefing_id: int, session: AsyncSession = Depends(get_session)
):
    """
    Delete a briefing by ID.

    Args:
        briefing_id: ID of the briefing to delete
        session: Database session

    Returns:
        Success message

    Raises:
        404: If briefing not found
    """
    stmt = select(Briefing).where(Briefing.id == briefing_id)
    result = await session.execute(stmt)
    briefing = result.scalar_one_or_none()

    if not briefing:
        raise HTTPException(
            status_code=404, detail=f"Briefing {briefing_id} not found"
        )

    await session.delete(briefing)
    await session.commit()

    return {"message": f"Briefing {briefing_id} deleted successfully"}
