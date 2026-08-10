"""Create configured search provider(s) without exposing credentials to the UI."""
from app.providers.search.composite import CompositeSearchProvider
from app.providers.search.google_cse import GoogleCSEProvider
from app.providers.search.http_providers import BraveProvider, SerperProvider, TavilyProvider
from app.providers.search.rss import RSSProvider


def _http_provider(settings):
    if settings.tavily_api_key:
        return TavilyProvider(settings.tavily_api_key, settings.request_timeout), "Tavily"
    if settings.brave_api_key:
        return BraveProvider(settings.brave_api_key, settings.request_timeout), "Brave Search"
    if settings.serper_api_key:
        return SerperProvider(settings.serper_api_key, settings.request_timeout), "Serper"
    if getattr(settings, "google_cse_api_key", None) and getattr(settings, "google_cse_id", None):
        return (
            GoogleCSEProvider(
                settings.google_cse_api_key,
                settings.google_cse_id,
                settings.request_timeout,
            ),
            "Google CSE",
        )
    return None, None


def configured_provider(settings, rss_urls: list[str] | None = None):
    http, http_name = _http_provider(settings)
    rss = RSSProvider(rss_urls) if rss_urls else None
    if http and rss:
        return CompositeSearchProvider([http, rss]), f"{http_name} + RSS"
    if http:
        return http, http_name
    if rss:
        return rss, "RSS"
    return None, None
