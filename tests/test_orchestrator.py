from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.agents.orchestrator import ResearchOrchestrator
from app.models.schemas import SearchResult


class FakeProvider:
    async def search(self, query, since=None, limit=20):
        now = datetime.now(UTC).replace(tzinfo=None)
        return [
            SearchResult(
                title="Newark school board meeting",
                url="https://newarknj.gov/schools/meeting",
                summary="Newark New Jersey parents invited to the school board meeting",
                source="City of Newark",
                published_at=now,
                reliability=0.9,
            ),
            SearchResult(
                title="Newark California festival",
                url="https://example.com/ca",
                summary="Festival in Newark California",
                source="Web",
                published_at=now,
            ),
        ]


@pytest.mark.asyncio
async def test_orchestrator_filters_and_ranks():
    group = SimpleNamespace(
        city="Newark",
        state="New Jersey",
        county="Essex County",
        excluded_keywords="",
        topics=[SimpleNamespace(name="school")],
    )
    ranked = await ResearchOrchestrator(FakeProvider()).run(group, topic="schools")
    assert ranked
    assert all("California" not in item.summary for _, _, item in ranked)
    assert ranked[0][0] >= ranked[-1][0]
