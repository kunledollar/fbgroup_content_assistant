import httpx

from app.models.schemas import SearchResult

from .base import SearchProvider


class GoogleCSEProvider(SearchProvider):
    endpoint = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: str, cse_id: str, timeout: float = 15):
        self.api_key = api_key
        self.cse_id = cse_id
        self.timeout = timeout

    async def search(self, query, since=None, limit=20):
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": min(limit, 10),
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            data = (await client.get(self.endpoint, params=params)).raise_for_status().json()
        return [
            SearchResult(
                title=x.get("title", "Untitled"),
                url=x.get("link"),
                summary=x.get("snippet", ""),
                source=x.get("displayLink", "Web"),
            )
            for x in data.get("items", [])
            if x.get("link")
        ]
