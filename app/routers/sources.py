"""API routes for managing watchlist sources."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, HttpUrl
from typing import List, Optional

from app.models.database import get_session
from app.models.source import Source, SourceType, SourceCategory

router = APIRouter(prefix="/api/sources", tags=["sources"])


# Pydantic schemas
class SourceCreate(BaseModel):
    """Schema for creating a new source."""
    name: str
    category: SourceCategory
    source_type: SourceType
    url: HttpUrl
    priority: int = 5
    active: bool = True


class SourceUpdate(BaseModel):
    """Schema for updating a source."""
    name: Optional[str] = None
    category: Optional[SourceCategory] = None
    source_type: Optional[SourceType] = None
    url: Optional[HttpUrl] = None
    priority: Optional[int] = None
    active: Optional[bool] = None


class SourceResponse(BaseModel):
    """Schema for source response."""
    id: int
    name: str
    category: str
    source_type: str
    url: str
    priority: int
    active: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=List[SourceResponse])
async def list_sources(
    active_only: bool = False,
    session: AsyncSession = Depends(get_session)
):
    """List all sources."""
    stmt = select(Source).order_by(Source.priority.desc(), Source.name)

    if active_only:
        stmt = stmt.where(Source.active == True)

    result = await session.execute(stmt)
    sources = result.scalars().all()
    return sources


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific source by ID."""
    result = await session.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return source


@router.post("/", response_model=SourceResponse, status_code=201)
async def create_source(
    source_data: SourceCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new source."""
    source = Source(
        name=source_data.name,
        category=source_data.category,
        source_type=source_data.source_type,
        url=str(source_data.url),
        priority=source_data.priority,
        active=source_data.active
    )

    session.add(source)
    await session.commit()
    await session.refresh(source)

    return source


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    source_data: SourceUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update a source."""
    result = await session.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Update only provided fields
    update_data = source_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "url":
            value = str(value)
        setattr(source, field, value)

    await session.commit()
    await session.refresh(source)

    return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete a source."""
    result = await session.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await session.delete(source)
    await session.commit()

    return None
