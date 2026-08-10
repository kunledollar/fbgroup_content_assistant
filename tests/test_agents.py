from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.agents.core import (
    DeduplicationAgent,
    FreshnessAgent,
    RankingAgent,
    RelevanceAgent,
    ReliabilityAgent,
)
from app.models.schemas import SearchResult


def result(title="Newark school meeting",url="https://newarknj.gov/a",**kw):return SearchResult(title=title,url=url,source="City",**kw)
def group():return SimpleNamespace(city="Newark",state="New Jersey",county="Essex County",excluded_keywords="",topics=[SimpleNamespace(name="school")])
def test_freshness_scoring():
    now=datetime.now(UTC);a=FreshnessAgent();assert a.score(now-timedelta(hours=4),now)==1;assert a.score(now-timedelta(days=40),now)==.1;assert a.score(None)==.15
def test_location_matching_rejects_wrong_newark():
    a=RelevanceAgent();assert a.score(result(summary="Newark California council"),group())==0;assert a.score(result(summary="Newark New Jersey school parents"),group())>.5
def test_deduplication():
    xs=[result("Newark Board meeting tonight","https://a.com/1"),result("Newark Board meeting tonight!","https://b.com/2")];assert len(DeduplicationAgent().deduplicate(xs))==1
def test_source_reliability():assert ReliabilityAgent().score(result())==.95
def test_ranking_is_transparent():
    score,why=RankingAgent().rank(result(),1,1,.95);assert 0<=score<=100;assert "freshness" in why and "source" in why
from app.utils.content import extract_date, topic_match


def test_date_extraction_and_topic_match():
    assert extract_date("Meeting August 12, 2026").date().isoformat()=="2026-08-12"
    assert topic_match("school parents meeting",["school","parents"])==1
