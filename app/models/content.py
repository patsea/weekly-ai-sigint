"""Content item model for fetched articles/posts."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class ContentItem(Base):
    """Fetched content item from a source."""

    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    content = Column(Text, nullable=True)  # Full text if available
    summary = Column(Text, nullable=True)  # Summary/excerpt
    published_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    # Deduplication constraint
    __table_args__ = (
        UniqueConstraint('url', name='uq_content_url'),
    )

    def __repr__(self):
        return f"<ContentItem(title='{self.title[:50]}...', url='{self.url}')>"
