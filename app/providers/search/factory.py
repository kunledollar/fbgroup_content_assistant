"""Create the first configured search provider without exposing credentials to the UI."""
from app.providers.search.http_providers import BraveProvider, SerperProvider, TavilyProvider


def configured_provider(settings):
    if settings.tavily_api_key:
        return TavilyProvider(settings.tavily_api_key, settings.request_timeout), "Tavily"
    if settings.brave_api_key:
        return BraveProvider(settings.brave_api_key, settings.request_timeout), "Brave Search"
    if settings.serper_api_key:
        return SerperProvider(settings.serper_api_key, settings.request_timeout), "Serper"
    return None, None
