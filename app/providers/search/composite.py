from .base import SearchProvider


class CompositeSearchProvider(SearchProvider):
    """Merge results from multiple providers; individual failures are skipped."""

    def __init__(self, providers: list):
        self.providers = [p for p in providers if p is not None]

    async def search(self, query, since=None, limit=20):
        results = []
        for provider in self.providers:
            try:
                results.extend(await provider.search(query, since=since, limit=limit))
            except Exception:
                continue
        return results
