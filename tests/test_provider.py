import httpx
import pytest

from app.providers.search.http_providers import TavilyProvider, _hostname


@pytest.mark.asyncio
async def test_provider_interface(monkeypatch):
    async def post(self, *a, **k):
        return httpx.Response(200, json={"results": []}, request=httpx.Request("POST", a[0]))

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    assert await TavilyProvider("test").search("Newark") == []


@pytest.mark.asyncio
async def test_tavily_skips_malformed_results(monkeypatch):
    payload = {
        "results": [
            {"title": "Good", "url": "https://newarknj.gov/notice", "content": "Local notice"},
            {"title": "Bad url", "url": None, "content": "x"},
            {"title": "Short", "url": "not-a-url", "content": "y"},
            {"title": None, "url": "https://example.com", "content": "z"},
        ]
    }

    async def post(self, *a, **k):
        return httpx.Response(200, json=payload, request=httpx.Request("POST", a[0]))

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    results = await TavilyProvider("test").search("Newark")
    assert len(results) == 1
    assert results[0].source == "newarknj.gov"


def test_hostname_helper():
    assert _hostname("https://www.example.com/a") == "example.com"
    assert _hostname("") == "Web"
    assert _hostname("not-a-url") == "Web"
