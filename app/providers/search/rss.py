import asyncio, feedparser
from datetime import datetime
from dateutil import parser
from app.models.schemas import SearchResult
from .base import SearchProvider
class RSSProvider(SearchProvider):
    def __init__(self, urls: list[str]): self.urls=urls
    async def search(self, query, since=None, limit=20):
        terms=set(query.lower().split())
        def load():
            out=[]
            for url in self.urls:
                feed=feedparser.parse(url)
                for x in feed.entries:
                    text=f"{x.get('title','')} {x.get('summary','')}".lower()
                    if not terms.intersection(text.split()): continue
                    dt=parser.parse(x.published).replace(tzinfo=None) if x.get("published") else None
                    if since and dt and dt < since: continue
                    out.append(SearchResult(title=x.title,url=x.link,summary=x.get('summary',''),source=feed.feed.get('title','RSS'),published_at=dt))
            return out[:limit]
        return await asyncio.to_thread(load)
