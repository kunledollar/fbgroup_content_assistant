from types import SimpleNamespace
from app.providers.search.factory import configured_provider
from app.providers.search.http_providers import BraveProvider, SerperProvider, TavilyProvider


def settings(**values):
    defaults={"tavily_api_key":None,"brave_api_key":None,"serper_api_key":None,"request_timeout":12}
    defaults.update(values);return SimpleNamespace(**defaults)


def test_factory_reports_missing_configuration():
    assert configured_provider(settings()) == (None, None)


def test_factory_selects_configured_providers_in_priority_order():
    provider,name=configured_provider(settings(tavily_api_key="t",brave_api_key="b"))
    assert isinstance(provider,TavilyProvider) and name=="Tavily"
    provider,name=configured_provider(settings(brave_api_key="b"))
    assert isinstance(provider,BraveProvider) and name=="Brave Search"
    provider,name=configured_provider(settings(serper_api_key="s"))
    assert isinstance(provider,SerperProvider) and name=="Serper"
