"""API routes for application settings management."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from pathlib import Path

from app.config import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    """Schema for settings response (with masked secrets)."""
    anthropic_api_key: str
    notion_token: str
    notion_page_id: str
    slack_webhook_url: str
    timezone: str
    weekly_run_day: int
    weekly_run_hour: int
    weekly_run_minute: int


class SettingsUpdate(BaseModel):
    """Schema for updating settings."""
    anthropic_api_key: Optional[str] = None
    notion_token: Optional[str] = None
    notion_page_id: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    timezone: Optional[str] = None
    weekly_run_day: Optional[int] = None
    weekly_run_hour: Optional[int] = None
    weekly_run_minute: Optional[int] = None


def mask_secret(value: Optional[str], show_chars: int = 4) -> str:
    """Mask a secret value, showing only last N characters."""
    if not value:
        return ""
    if len(value) <= show_chars:
        return "*" * len(value)
    return "*" * (len(value) - show_chars) + value[-show_chars:]


@router.get("/", response_model=SettingsResponse)
async def get_settings():
    """
    Get current settings with masked secrets.

    Returns:
        Current application settings with API keys/tokens masked
    """
    return SettingsResponse(
        anthropic_api_key=mask_secret(settings.ANTHROPIC_API_KEY),
        notion_token=mask_secret(settings.NOTION_TOKEN),
        notion_page_id=settings.NOTION_PAGE_ID or "",
        slack_webhook_url=mask_secret(settings.SLACK_WEBHOOK_URL, show_chars=10),
        timezone=settings.TIMEZONE,
        weekly_run_day=settings.WEEKLY_RUN_DAY,
        weekly_run_hour=settings.WEEKLY_RUN_HOUR,
        weekly_run_minute=settings.WEEKLY_RUN_MINUTE,
    )


@router.post("/")
async def update_settings(settings_update: SettingsUpdate):
    """
    Update application settings by modifying .env file.

    Args:
        settings_update: Settings to update (only provided fields will be updated)

    Returns:
        Success message

    Note:
        Server restart required for changes to take effect
    """
    env_file = Path(".env")

    if not env_file.exists():
        raise HTTPException(
            status_code=404,
            detail=".env file not found. Create one from .env.example"
        )

    # Read current .env content
    env_lines = env_file.read_text().splitlines()
    updated_lines = []
    keys_to_update = {}

    # Build update dict (only non-None values)
    update_data = settings_update.model_dump(exclude_unset=True)

    # Map Pydantic field names to env var names
    field_to_env = {
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "notion_token": "NOTION_TOKEN",
        "notion_page_id": "NOTION_PAGE_ID",
        "slack_webhook_url": "SLACK_WEBHOOK_URL",
        "timezone": "TIMEZONE",
        "weekly_run_day": "WEEKLY_RUN_DAY",
        "weekly_run_hour": "WEEKLY_RUN_HOUR",
        "weekly_run_minute": "WEEKLY_RUN_MINUTE",
    }

    for field_name, value in update_data.items():
        env_name = field_to_env.get(field_name)
        if env_name:
            keys_to_update[env_name] = value

    # Update existing lines
    updated_keys = set()
    for line in env_lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=")[0].strip()
            if key in keys_to_update:
                updated_lines.append(f"{key}={keys_to_update[key]}")
                updated_keys.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Add new keys that weren't in the file
    for key, value in keys_to_update.items():
        if key not in updated_keys:
            updated_lines.append(f"{key}={value}")

    # Write back to .env
    env_file.write_text("\n".join(updated_lines) + "\n")

    return {
        "message": "Settings updated successfully. Restart server for changes to take effect.",
        "updated_keys": list(keys_to_update.keys())
    }


@router.post("/test-connections")
async def test_connections():
    """
    Test external service connections.

    Returns:
        Status of each configured service
    """
    results = {
        "anthropic": False,
        "notion": False,
        "slack": False,
    }

    # Test Anthropic API
    if settings.ANTHROPIC_API_KEY:
        try:
            # Simple check - just verify key format
            results["anthropic"] = settings.ANTHROPIC_API_KEY.startswith("sk-ant-")
        except Exception:
            pass

    # Test Notion
    if settings.NOTION_TOKEN and settings.NOTION_PAGE_ID:
        try:
            results["notion"] = (
                settings.NOTION_TOKEN.startswith("secret_") and
                len(settings.NOTION_PAGE_ID) > 0
            )
        except Exception:
            pass

    # Test Slack
    if settings.SLACK_WEBHOOK_URL:
        try:
            results["slack"] = settings.SLACK_WEBHOOK_URL.startswith("https://hooks.slack.com")
        except Exception:
            pass

    return {
        "results": results,
        "message": "Basic format validation completed. Run actual operations to fully test."
    }
