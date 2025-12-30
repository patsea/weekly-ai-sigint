"""API routes for viewing fetched content."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.models.database import get_session
from app.models.content import ContentItem
from app.services.fetcher import get_recent_content

router = APIRouter(prefix="/api/content", tags=["content"])


# Pydantic schemas
class ContentItemResponse(BaseModel):
    """Schema for content item response."""
    id: int
    source_id: int
    title: str
    url: str
    summary: Optional[str]
    published_at: Optional[datetime]
    fetched_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ContentItemResponse])
async def list_content(
    limit: int = 50,
    source_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    List recent content items.

    Args:
        limit: Maximum number of items (default 50, max 200)
        source_id: Optional filter by source ID
    """
    # Cap limit at 200
    limit = min(limit, 200)

    items = await get_recent_content(session, limit=limit, source_id=source_id)
    return items


@router.get("/{content_id}", response_model=ContentItemResponse)
async def get_content_item(
    content_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific content item by ID."""
    result = await session.execute(
        select(ContentItem).where(ContentItem.id == content_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")

    return item
