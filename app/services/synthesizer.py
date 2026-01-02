"""Content synthesis service using Claude AI."""
import anthropic
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, Dict
from pathlib import Path

from app.models.content import ContentItem
from app.models.briefing import Briefing
from app.models.source import Source
from app.config import settings


class SynthesizerService:
    """Service for synthesizing content into briefings using Claude."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def synthesize_briefing(self, days_back: int = 7) -> Briefing:
        """
        Generate briefing from recent content.

        Args:
            days_back: Number of days to look back for content

        Returns:
            Created Briefing object
        """
        # 1. Gather content from the specified time period
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        stmt = (
            select(ContentItem)
            .where(ContentItem.fetched_at >= cutoff)
            .order_by(ContentItem.published_at.desc())
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()

        if not items:
            raise ValueError(f"No content found in the last {days_back} days")

        # 2. Load sources for these items
        source_ids = list(set(item.source_id for item in items))
        sources_stmt = select(Source).where(Source.id.in_(source_ids))
        sources_result = await self.session.execute(sources_stmt)
        sources = sources_result.scalars().all()
        sources_by_id = {source.id: source for source in sources}

        # 3. Format content for Claude
        content_text = self._format_content_for_synthesis(items, sources_by_id)

        # 3. Load prompt template
        prompt_template = self._load_prompt_template()

        # 4. Call Claude API
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt_template}\n\n---\n\nCONTENT TO SYNTHESIZE:\n\n{content_text}",
                }
            ],
        )

        briefing_content = message.content[0].text

        # 5. Create briefing record
        week_end = datetime.now(timezone.utc)
        week_start = week_end - timedelta(days=days_back)

        briefing = Briefing(
            title=f"Sunday Briefing Pack - {week_start.strftime('%b %d')} to {week_end.strftime('%b %d, %Y')}",
            week_start=week_start,
            week_end=week_end,
            content=briefing_content,
        )

        self.session.add(briefing)
        await self.session.commit()
        # Refresh briefing with content_items relationship loaded
        await self.session.refresh(briefing, ["content_items"])

        # 6. Link content items to briefing (many-to-many relationship)
        for item in items:
            briefing.content_items.append(item)
        await self.session.commit()

        return briefing

    def _format_content_for_synthesis(
        self, items: list[ContentItem], sources_by_id: Dict[int, Source]
    ) -> str:
        """
        Format content items into text for Claude.

        Args:
            items: List of ContentItem objects
            sources_by_id: Dictionary mapping source IDs to Source objects

        Returns:
            Formatted string with all content
        """
        sections = []

        for item in items:
            section = f"### {item.title}\n"

            # Get source name from lookup
            source = sources_by_id.get(item.source_id)
            source_name = source.name if source else "Unknown"
            section += f"**Source:** {source_name}\n"

            if item.published_at:
                section += f"**Date:** {item.published_at.strftime('%Y-%m-%d')}\n"

            section += f"**URL:** {item.url}\n\n"

            # Include summary or truncated content
            if item.summary:
                content_preview = item.summary[:1500]
                if len(item.summary) > 1500:
                    content_preview += "..."
                section += f"{content_preview}\n\n"

            section += "---\n"
            sections.append(section)

        return "\n".join(sections)

    def _load_prompt_template(self) -> str:
        """
        Load prompt template from file.

        Returns:
            Prompt template text
        """
        prompt_path = Path("prompts/sunday_briefing.md")

        if prompt_path.exists():
            return prompt_path.read_text()

        # Fallback prompt if template doesn't exist
        return """You are an expert analyst. Synthesize the following content into a
comprehensive weekly briefing with key developments, emerging patterns, and notable mentions.
Focus on strategic implications and actionable insights."""


async def synthesize_weekly_briefing(
    session: AsyncSession, days_back: int = 7
) -> Briefing:
    """
    Convenience function to synthesize a briefing.

    Args:
        session: Database session
        days_back: Number of days to include

    Returns:
        Created Briefing object
    """
    service = SynthesizerService(session)
    return await service.synthesize_briefing(days_back)
