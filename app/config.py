"""Application configuration from environment variables."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # AI Integration
    ANTHROPIC_API_KEY: str

    # Notion Integration
    NOTION_TOKEN: Optional[str] = None
    NOTION_PAGE_ID: Optional[str] = None

    # Slack Integration
    SLACK_WEBHOOK_URL: Optional[str] = None

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/briefings.db"

    # Security
    SECRET_KEY: str

    # Timezone
    TIMEZONE: str = "Europe/Madrid"

    # Scheduler
    WEEKLY_RUN_DAY: int = 6  # Sunday = 6
    WEEKLY_RUN_HOUR: int = 8
    WEEKLY_RUN_MINUTE: int = 0

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
