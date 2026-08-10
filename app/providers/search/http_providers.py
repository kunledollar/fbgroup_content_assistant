from datetime import datetime

import httpx

from app.models.schemas import SearchResult

from .base import SearchProvider


class ApiSearchProvider(SearchProvider):
    endpoint = ""; key_header = ""
    def __init__(self, api_key: str, timeout: float = 15): self.api_key, self.timeout = api_key, timeout

class TavilyProvider(ApiSearchProvider):
    endpoint = "https://api.tavily.com/search"
    async def search(self, query, since=None, limit=20):
        payload = {"api_key": self.api_key, "query": query, "max_results": limit, "search_depth": "advanced"}
        if since:
            payload["days"] = max(1, (datetime.now() - since.replace(tzinfo=None)).days + 1)
        async with httpx.AsyncClient(timeout=self.timeout) as client: data=(await client.post(self.endpoint,json=payload)).raise_for_status().json()
        return [SearchResult(title=x["title"],url=x["url"],summary=x.get("content", ""),source=x.get("url", "").split("/")[2]) for x in data.get("results", [])]

class BraveProvider(ApiSearchProvider):
    endpoint = "https://api.search.brave.com/res/v1/web/search"
    async def search(self, query, since=None, limit=20):
        headers={"X-Subscription-Token":self.api_key,"Accept":"application/json"}
        async with httpx.AsyncClient(timeout=self.timeout) as client: data=(await client.get(self.endpoint,params={"q":query,"count":limit},headers=headers)).raise_for_status().json()
        return [SearchResult(title=x["title"],url=x["url"],summary=x.get("description", ""),source=x.get("profile",{}).get("long_name","Web")) for x in data.get("web",{}).get("results",[])]

class SerperProvider(ApiSearchProvider):
    endpoint="https://google.serper.dev/search"
    async def search(self, query, since=None, limit=20):
        async with httpx.AsyncClient(timeout=self.timeout) as client: data=(await client.post(self.endpoint,json={"q":query,"num":limit},headers={"X-API-KEY":self.api_key})).raise_for_status().json()
        return [SearchResult(title=x["title"],url=x["link"],summary=x.get("snippet", ""),source=x.get("source","Web")) for x in data.get("organic",[])]
