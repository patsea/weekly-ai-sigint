"""Notion export service for weekly briefings."""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func

from app.config import settings
from app.models.briefing import Briefing

logger = logging.getLogger(__name__)


class NotionExportError(Exception):
    """Raised when Notion export fails."""
    pass


async def export_briefing_to_notion(
    session: AsyncSession,
    briefing_id: Optional[int] = None
) -> dict:
    """
    Export a briefing to Notion.

    Args:
        session: Database session
        briefing_id: ID of briefing to export (None = latest)

    Returns:
        Dict with export result:
        {
            "success": bool,
            "briefing_id": int,
            "notion_page_id": str,
            "notion_url": str
        }

    Raises:
        NotionExportError: If export fails
        ValueError: If no briefing found or Notion not configured
    """
    # Validate Notion configuration
    if not settings.NOTION_TOKEN:
        raise ValueError("NOTION_TOKEN not configured in environment")
    if not settings.NOTION_PAGE_ID:
        raise ValueError("NOTION_PAGE_ID not configured in environment")

    # Get briefing
    if briefing_id:
        stmt = select(Briefing).where(Briefing.id == briefing_id)
    else:
        # Get latest briefing
        stmt = select(Briefing).order_by(Briefing.created_at.desc()).limit(1)

    result = await session.execute(stmt)
    briefing = result.scalar_one_or_none()

    if not briefing:
        raise ValueError(
            f"No briefing found{f' with ID {briefing_id}' if briefing_id else ''}"
        )

    try:
        # Import Notion client here to fail gracefully if not installed
        try:
            from notion_client import Client
        except ImportError:
            raise NotionExportError(
                "notion-client not installed. Run: pip install notion-client"
            )

        # Initialize Notion client
        notion = Client(auth=settings.NOTION_TOKEN)

        # Create page title
        page_title = f"{briefing.title} — Week of {briefing.week_start.strftime('%b %d, %Y')}"

        # Build Notion blocks from briefing content
        blocks = _markdown_to_notion_blocks(briefing.content)

        # Notion API limits children to 100 blocks per request
        # If we have more, we need to create the page with first 100,
        # then append the rest in batches
        initial_blocks = blocks[:100]
        remaining_blocks = blocks[100:]

        # Create page under parent page with first 100 blocks
        response = notion.pages.create(
            parent={"page_id": settings.NOTION_PAGE_ID},
            properties={
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": page_title
                            }
                        }
                    ]
                }
            },
            children=initial_blocks
        )

        notion_page_id = response["id"]

        # Append remaining blocks in batches of 100
        if remaining_blocks:
            for i in range(0, len(remaining_blocks), 100):
                batch = remaining_blocks[i:i + 100]
                notion.blocks.children.append(
                    block_id=notion_page_id,
                    children=batch
                )

        notion_url = response["url"]

        # Update briefing with Notion metadata
        await session.execute(
            update(Briefing)
            .where(Briefing.id == briefing.id)
            .values(
                notion_page_id=notion_page_id,
                notion_url=notion_url,
                notion_exported_at=func.now()
            )
        )
        await session.commit()

        logger.info(
            f"Exported briefing {briefing.id} to Notion: {notion_url}"
        )

        return {
            "success": True,
            "briefing_id": briefing.id,
            "notion_page_id": notion_page_id,
            "notion_url": notion_url
        }

    except Exception as e:
        logger.error(f"Notion export failed: {str(e)}")
        raise NotionExportError(f"Failed to export to Notion: {str(e)}")


def _markdown_to_notion_blocks(markdown_content: str) -> list:
    """
    Convert markdown content to Notion blocks.

    This is a simple implementation that handles:
    - Headings (# ## ###)
    - Paragraphs
    - Bullet lists

    Args:
        markdown_content: Markdown formatted text

    Returns:
        List of Notion block objects
    """
    blocks = []
    lines = markdown_content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # Heading 1
        if line.startswith('# '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                }
            })
        # Heading 2
        elif line.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                }
            })
        # Heading 3
        elif line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                }
            })
        # Bullet list
        elif line.startswith('- ') or line.startswith('* '):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                }
            })
        # Paragraph (split long text into chunks if > 2000 chars)
        else:
            text = line
            # Notion text blocks have 2000 char limit
            while text:
                chunk = text[:2000]
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                })
                text = text[2000:]

        i += 1

    return blocks
