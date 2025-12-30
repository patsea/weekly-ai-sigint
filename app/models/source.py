"""Watchlist source model."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
from .database import Base


class SourceType(str, enum.Enum):
    """Types of content sources."""

    RSS = "rss"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    BLOG = "blog"
    COMPANY = "company"
    NEWSLETTER = "newsletter"


class SourceCategory(str, enum.Enum):
    """Categories for organizing sources."""

    NEWSLETTER = "newsletter"
    PERSON = "person"
    ORGANIZATION = "organization"
    MEDIA = "media"
    RESEARCH = "research"


class Source(Base):
    """Watchlist source model."""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(SQLEnum(SourceCategory), nullable=False)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    url = Column(String, nullable=False)
    priority = Column(Integer, default=5)  # 1-10 scale
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Source(name='{self.name}', category='{self.category}', type='{self.source_type}')>"
