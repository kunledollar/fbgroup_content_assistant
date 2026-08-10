from datetime import datetime
from urllib.parse import urlparse

import httpx

from app.models.schemas import SearchResult

from .base import SearchProvider


def _hostname(url: str, fallback: str = "Web") -> str:
    host = urlparse(url).netloc or ""
    host = host.removeprefix("www.")
    return host or fallback


def _to_result(title: str | None, url: str | None, summary: str = "", source: str | None = None):
    if not title or not url:
        return None
    try:
        return SearchResult(
            title=title,
            url=url,
            summary=summary or "",
            source=source or _hostname(url),
        )
    except Exception:
        return None


class ApiSearchProvider(SearchProvider):
    endpoint = ""
    key_header = ""

    def __init__(self, api_key: str, timeout: float = 15):
        self.api_key, self.timeout = api_key, timeout


class TavilyProvider(ApiSearchProvider):
    endpoint = "https://api.tavily.com/search"

    async def search(self, query, since=None, limit=20):
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": limit,
            "search_depth": "basic",
        }
        if since:
            payload["days"] = max(1, (datetime.now() - since.replace(tzinfo=None)).days + 1)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            data = (await client.post(self.endpoint, json=payload)).raise_for_status().json()
        out = []
        for item in data.get("results", []) or []:
            parsed = _to_result(
                item.get("title"),
                item.get("url"),
                item.get("content", ""),
                _hostname(item.get("url", "")),
            )
            if parsed:
                out.append(parsed)
        return out


class BraveProvider(ApiSearchProvider):
    endpoint = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query, since=None, limit=20):
        headers = {"X-Subscription-Token": self.api_key, "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            data = (
                await client.get(self.endpoint, params={"q": query, "count": limit}, headers=headers)
            ).raise_for_status().json()
        out = []
        for item in data.get("web", {}).get("results", []) or []:
            parsed = _to_result(
                item.get("title"),
                item.get("url"),
                item.get("description", ""),
                item.get("profile", {}).get("long_name") or _hostname(item.get("url", "")),
            )
            if parsed:
                out.append(parsed)
        return out


class SerperProvider(ApiSearchProvider):
    endpoint = "https://google.serper.dev/search"

    async def search(self, query, since=None, limit=20):
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            data = (
                await client.post(
                    self.endpoint,
                    json={"q": query, "num": limit},
                    headers={"X-API-KEY": self.api_key},
                )
            ).raise_for_status().json()
        out = []
        for item in data.get("organic", []) or []:
            parsed = _to_result(
                item.get("title"),
                item.get("link"),
                item.get("snippet", ""),
                item.get("source") or _hostname(item.get("link", "")),
            )
            if parsed:
                out.append(parsed)
        return out
