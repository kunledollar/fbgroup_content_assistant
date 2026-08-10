from datetime import datetime

from sqlalchemy.orm import Session

from app.database.bootstrap import initialize
from app.database.session import make_engine
from app.models.schemas import SearchResult
from app.repositories.core import SourceRepository, StoryRepository


def test_source_and_story_repositories():
    engine = make_engine("sqlite://")
    initialize(engine)
    with Session(engine) as session:
        sources = SourceRepository(session)
        assert len(sources.all()) == 4
        assert any(url for url in sources.enabled_rss_urls())

        stories = StoryRepository(session)
        result = SearchResult(
            title="Newark housing hearing",
            url="https://newarknj.gov/housing-hearing",
            summary="Residents may attend the public hearing",
            source="City of Newark",
            published_at=datetime(2026, 8, 1),
            reliability=0.95,
        )
        story = stories.upsert_from_result(result, 88.0, "freshness 100%", topic="Housing")
        assert story.id
        again = stories.upsert_from_result(result, 91.0, "freshness 100%; local 90%", topic="Housing")
        assert again.id == story.id
        assert again.score == 91.0
        stories.set_saved(again, True)
        assert stories.saved()[0].title.startswith("Newark housing")
        assert stories.by_topic("Housing")
