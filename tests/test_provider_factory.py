from types import SimpleNamespace

from app.providers.search.composite import CompositeSearchProvider
from app.providers.search.factory import configured_provider
from app.providers.search.google_cse import GoogleCSEProvider
from app.providers.search.http_providers import BraveProvider, SerperProvider, TavilyProvider
from app.providers.search.rss import RSSProvider


def settings(**values):
    defaults = {
        "tavily_api_key": None,
        "brave_api_key": None,
        "serper_api_key": None,
        "google_cse_api_key": None,
        "google_cse_id": None,
        "request_timeout": 12,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def test_factory_reports_missing_configuration():
    assert configured_provider(settings()) == (None, None)


def test_factory_selects_configured_providers_in_priority_order():
    provider, name = configured_provider(settings(tavily_api_key="t", brave_api_key="b"))
    assert isinstance(provider, TavilyProvider) and name == "Tavily"
    provider, name = configured_provider(settings(brave_api_key="b"))
    assert isinstance(provider, BraveProvider) and name == "Brave Search"
    provider, name = configured_provider(settings(serper_api_key="s"))
    assert isinstance(provider, SerperProvider) and name == "Serper"
    provider, name = configured_provider(settings(google_cse_api_key="g", google_cse_id="cx"))
    assert isinstance(provider, GoogleCSEProvider) and name == "Google CSE"


def test_factory_uses_rss_and_composites_with_http():
    provider, name = configured_provider(settings(), rss_urls=["https://example.org/feed.xml"])
    assert isinstance(provider, RSSProvider) and name == "RSS"
    provider, name = configured_provider(
        settings(tavily_api_key="t"), rss_urls=["https://example.org/feed.xml"]
    )
    assert isinstance(provider, CompositeSearchProvider) and name == "Tavily + RSS"
