"""Slack notification service for weekly briefings."""
import logging
import httpx
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func

from app.config import settings
from app.models.briefing import Briefing

logger = logging.getLogger(__name__)


class SlackNotifyError(Exception):
    """Raised when Slack notification fails."""
    pass


async def send_briefing_to_slack(
    session: AsyncSession,
    briefing_id: Optional[int] = None
) -> dict:
    """
    Send a briefing notification to Slack via webhook.

    Args:
        session: Database session
        briefing_id: ID of briefing to notify (None = latest)

    Returns:
        Dict with notification result:
        {
            "success": bool,
            "briefing_id": int,
            "message": str
        }

    Raises:
        SlackNotifyError: If notification fails
        ValueError: If no briefing found or Slack not configured
    """
    # Validate Slack configuration
    if not settings.SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL not configured in environment")

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
        # Extract summary/highlights from content (first 500 chars or first section)
        summary = _extract_summary(briefing.content)

        # Build Slack message payload
        payload = _build_slack_message(briefing, summary)

        # Send to Slack webhook
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.SLACK_WEBHOOK_URL,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()

        # Update briefing with Slack timestamp
        await session.execute(
            update(Briefing)
            .where(Briefing.id == briefing.id)
            .values(slack_sent_at=func.now())
        )
        await session.commit()

        logger.info(
            f"Sent Slack notification for briefing {briefing.id}"
        )

        return {
            "success": True,
            "briefing_id": briefing.id,
            "message": "Notification sent to Slack"
        }

    except httpx.HTTPError as e:
        logger.error(f"Slack HTTP error: {str(e)}")
        raise SlackNotifyError(f"Failed to send to Slack: {str(e)}")
    except Exception as e:
        logger.error(f"Slack notification failed: {str(e)}")
        raise SlackNotifyError(f"Failed to send to Slack: {str(e)}")


def _extract_summary(content: str, max_length: int = 500) -> str:
    """
    Extract a summary from briefing content.

    Takes the first paragraph or section up to max_length characters.

    Args:
        content: Full briefing content
        max_length: Maximum summary length

    Returns:
        Summary text
    """
    lines = content.split('\n')

    summary_lines = []
    char_count = 0

    for line in lines:
        line = line.strip()

        # Skip empty lines and markdown headers
        if not line or line.startswith('#'):
            continue

        # Add line if within limit
        if char_count + len(line) <= max_length:
            summary_lines.append(line)
            char_count += len(line) + 1  # +1 for newline
        else:
            # Add truncated line and break
            remaining = max_length - char_count
            if remaining > 50:  # Only add if meaningful
                summary_lines.append(line[:remaining] + "...")
            break

    return '\n'.join(summary_lines) if summary_lines else content[:max_length] + "..."


def _build_slack_message(briefing: Briefing, summary: str) -> dict:
    """
    Build Slack message payload in Block Kit format.

    Args:
        briefing: Briefing model
        summary: Extracted summary text

    Returns:
        Slack webhook payload dict
    """
    week_str = briefing.week_start.strftime("%B %d, %Y")

    # Build rich message with blocks
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📰 {briefing.title}",
                "emoji": True
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Week of *{week_str}* | {len(briefing.content_items)} items analyzed"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": summary
            }
        }
    ]

    # Add Notion link if available
    if briefing.notion_page_id:
        # Notion URLs format: https://notion.so/{page_id}
        notion_url = f"https://notion.so/{briefing.notion_page_id.replace('-', '')}"
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📖 Read Full Briefing on Notion",
                        "emoji": True
                    },
                    "url": notion_url,
                    "style": "primary"
                }
            ]
        })

    return {
        "blocks": blocks,
        # Fallback text for notifications
        "text": f"{briefing.title} — Week of {week_str}"
    }
