from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

class CommunityGroup(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    city: Mapped[str] = mapped_column(String(80)); county: Mapped[str] = mapped_column(String(80), default="")
    state: Mapped[str] = mapped_column(String(40), default="New Jersey")
    neighborhoods: Mapped[str] = mapped_column(Text, default=""); keywords: Mapped[str] = mapped_column(Text, default="")
    excluded_keywords: Mapped[str] = mapped_column(Text, default="")
    tone: Mapped[str] = mapped_column(String(30), default="Community"); post_length: Mapped[str] = mapped_column(String(20), default="Standard")
    facebook_url: Mapped[str | None] = mapped_column(String(500)); topics: Mapped[list[GroupTopic]] = relationship(cascade="all, delete-orphan")

class GroupTopic(Base):
    __tablename__ = "group_topics"; id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id")); name: Mapped[str] = mapped_column(String(120))

class Source(Base):
    __tablename__ = "sources"; id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160)); category: Mapped[str] = mapped_column(String(60), default="Community")
    website_url: Mapped[str] = mapped_column(String(500)); rss_url: Mapped[str | None] = mapped_column(String(500))
    priority: Mapped[int] = mapped_column(Integer, default=50); enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class Story(Base):
    __tablename__ = "stories"; id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500)); summary: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(1000), unique=True); source_name: Mapped[str] = mapped_column(String(200))
    published_at: Mapped[datetime | None] = mapped_column(DateTime); event_at: Mapped[datetime | None] = mapped_column(DateTime)
    location: Mapped[str] = mapped_column(String(200), default=""); topic: Mapped[str] = mapped_column(String(100), default="Community")
    score: Mapped[float] = mapped_column(Float, default=0); score_reason: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[str] = mapped_column(String(20), default="Unverified")

class GeneratedPost(Base):
    __tablename__ = "generated_posts"; id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id")); story_id: Mapped[int | None] = mapped_column(ForeignKey("stories.id"))
    headline: Mapped[str] = mapped_column(String(500)); body: Mapped[str] = mapped_column(Text); sources_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(30), default="Draft"); notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Setting(Base):
    __tablename__ = "settings"; key: Mapped[str] = mapped_column(String(100), primary_key=True); value: Mapped[str] = mapped_column(Text)
