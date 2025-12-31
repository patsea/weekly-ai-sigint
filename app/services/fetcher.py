"""Content fetching service for RSS feeds and web content."""
import feedparser
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.source import Source, SourceType
from app.models.content import ContentItem


async def fetch_from_source(source: Source, session: AsyncSession) -> Dict[str, Any]:
    """
    Fetch content from a single source.

    Returns:
        Dict with fetched, new, duplicate, and error counts
    """
    result = {
        "source_id": source.id,
        "source_name": source.name,
        "fetched": 0,
        "new": 0,
        "duplicates": 0,
        "errors": []
    }

    try:
        if source.source_type == SourceType.RSS:
            await _fetch_rss(source, session, result)
        elif source.source_type == SourceType.BLOG:
            await _fetch_blog(source, session, result)
        else:
            result["errors"].append(f"Unsupported source type: {source.source_type}")
    except Exception as e:
        result["errors"].append(f"Fetch error: {str(e)}")

    return result


async def _fetch_rss(source: Source, session: AsyncSession, result: Dict[str, Any]):
    """Fetch content from RSS feed."""
    # Store source_id early to avoid lazy loading issues
    source_id = source.id

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(source.url)
        response.raise_for_status()

        # Parse RSS feed
        feed = feedparser.parse(response.text)

        # Process each entry
        for entry in feed.entries:
            result["fetched"] += 1

            # Extract data
            title = entry.get("title", "Untitled")
            url = entry.get("link", "")
            summary = entry.get("summary", entry.get("description", ""))

            # Parse published date
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            # Check if URL already exists
            existing = await session.execute(
                select(ContentItem).where(ContentItem.url == url)
            )
            if existing.scalar_one_or_none():
                result["duplicates"] += 1
                continue

            # Create and add new content item
            content_item = ContentItem(
                source_id=source_id,
                title=title,
                url=url,
                summary=summary,
                published_at=published_at
            )
            session.add(content_item)
            result["new"] += 1

        # Commit all new items at once
        await session.commit()


async def _fetch_blog(source: Source, session: AsyncSession, result: Dict[str, Any]):
    """Fetch content from blog (basic implementation)."""
    # For now, treat blogs like RSS feeds
    # In a more advanced implementation, we could scrape HTML
    await _fetch_rss(source, session, result)


async def fetch_from_all_sources(session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Fetch content from all active sources.

    Returns:
        List of results from each source
    """
    # Get all active sources
    stmt = select(Source).where(Source.active == True).order_by(Source.priority.desc())
    result = await session.execute(stmt)
    sources = result.scalars().all()

    results = []
    for source in sources:
        source_result = await fetch_from_source(source, session)
        results.append(source_result)

    return results


async def get_recent_content(
    session: AsyncSession,
    limit: int = 50,
    source_id: Optional[int] = None
) -> List[ContentItem]:
    """
    Get recent content items.

    Args:
        session: Database session
        limit: Maximum number of items to return
        source_id: Optional filter by source

    Returns:
        List of content items ordered by fetched_at descending
    """
    stmt = select(ContentItem).order_by(ContentItem.fetched_at.desc()).limit(limit)

    if source_id:
        stmt = stmt.where(ContentItem.source_id == source_id)

    result = await session.execute(stmt)
    return result.scalars().all()
