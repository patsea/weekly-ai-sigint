"""Briefing model for synthesized weekly reports."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


# Junction table for many-to-many relationship
briefing_sources = Table(
    'briefing_sources',
    Base.metadata,
    Column('briefing_id', Integer, ForeignKey('briefings.id'), primary_key=True),
    Column('content_item_id', Integer, ForeignKey('content_items.id'), primary_key=True),
)


class BriefingSource(Base):
    """Alias for the junction table (for clarity in imports)."""

    __table__ = briefing_sources


class Briefing(Base):
    """Weekly synthesized briefing."""

    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)  # Synthesized briefing text
    week_start = Column(DateTime(timezone=True), nullable=False)
    week_end = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Notion/Slack export tracking
    notion_page_id = Column(String, nullable=True)
    notion_exported_at = Column(DateTime(timezone=True), nullable=True)
    slack_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Many-to-many relationship with content items
    content_items = relationship(
        "ContentItem",
        secondary=briefing_sources,
        backref="briefings"
    )

    def __repr__(self):
        return f"<Briefing(title='{self.title}', week={self.week_start.date()})>"
