from datetime import datetime
from pydantic import BaseModel, HttpUrl

class SearchResult(BaseModel):
    title: str; url: HttpUrl; summary: str = ""; source: str; published_at: datetime | None = None
    event_at: datetime | None = None; location: str = ""; topic: str = "Community"
    reliability: float = 0.5; local_relevance: float = 0.0

class PostDraft(BaseModel):
    headline: str; body: str; warnings: list[str] = []
