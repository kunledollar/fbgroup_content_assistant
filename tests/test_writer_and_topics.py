from types import SimpleNamespace

from app.models.entities import CommunityGroup
from app.models.schemas import SearchResult
from app.providers.images import ImageProvider
from app.providers.llm.openai_writer import OpenAIPostWriter
from app.services.writer import SafePostWriter
from app.utils.dates import since_for_range
from app.utils.topics import classify_topic


def test_paste_writer_sanitizes_and_marks_unverified():
    group = CommunityGroup(name="Community", city="Newark", county="Essex", state="New Jersey")
    draft = SafePostWriter().from_paste(
        "<script>alert(1)</script><p>Ward meeting tonight about housing</p>",
        group,
    )
    assert "UNVERIFIED COMMUNITY REPORT" in draft.body
    assert "script" not in draft.body.lower()
    assert "Ward meeting" in draft.body


def test_openai_writer_falls_back_without_key():
    story = SearchResult(
        title="Council notice",
        url="https://newarknj.gov/notice",
        source="City of Newark",
        summary="Public meeting scheduled",
        reliability=0.95,
    )
    group = CommunityGroup(name="Community", city="Newark", county="Essex", state="New Jersey")
    draft = OpenAIPostWriter(None).generate(story, group)
    assert "Council notice" in draft.body
    assert "newarknj.gov" in draft.body


def test_topic_classification_and_date_ranges():
    assert classify_topic("Board of Education parents meeting") == "Schools & Parents"
    assert classify_topic("NJ Transit bus advisory") == "Transportation"
    assert since_for_range("Last 7 Days") is not None
    assert since_for_range("Custom Date Range", 14) is not None


def test_image_provider_never_auto_downloads_news_photos():
    story = SimpleNamespace(title="Local crime report", url="https://news.example/photo", source="News")
    suggestion = ImageProvider().suggest(story, SimpleNamespace(city="Newark"))
    assert suggestion.source_url is None
    assert "never downloaded" in suggestion.note.lower() or "Not selected" in suggestion.license
