import httpx,pytest
from app.providers.search.http_providers import TavilyProvider
@pytest.mark.asyncio
async def test_provider_interface(monkeypatch):
    async def post(self,*a,**k):return httpx.Response(200,json={"results":[]},request=httpx.Request("POST",a[0]))
    monkeypatch.setattr(httpx.AsyncClient,"post",post);assert await TavilyProvider("test").search("Newark")==[]
