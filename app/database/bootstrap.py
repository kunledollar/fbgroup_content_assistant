from sqlalchemy import select, text

from app.database.session import Base
from app.models.entities import CommunityGroup, GroupTopic, Source

STARTERS = [
    ("Newark NJ Central Ward Community Issues & Complaints", "Newark", "Essex County", ["Central Ward", "complaints", "government"]),
    ("Essex County Community Leaders Network", "Newark", "Essex County", ["government", "community programs", "events"]),
    ("West Orange Civic Voice", "West Orange", "Essex County", ["government", "schools", "development"]),
    ("NEWARK HOUSING & TENANT RIGHTS", "Newark", "Essex County", ["affordable housing", "tenants", "eviction", "rent control", "Newark Housing Authority", "code enforcement"]),
    ("NEWARK NEIGHBORHOOD WATCH & PUBLIC SAFETY", "Newark", "Essex County", ["public safety", "police", "fire", "community alerts"]),
    ("Newark South Ward Community Issues & Complaints", "Newark", "Essex County", ["South Ward", "complaints", "government"]),
    ("NEWARK SCHOOLS & EDUCATION ISSUES", "Newark", "Essex County", ["Newark Public Schools", "Board of Education", "parents", "students", "school safety"]),
    ("NEWARK PUBLIC TRANSPORTATION, TRAIN, BUSES & TRAFFIC ISSUES", "Newark", "Essex County", ["NJ Transit", "PATH", "Newark Penn Station", "buses", "traffic", "road closures"]),
    ("Newark East Ward Community Issues & Complaints", "Newark", "Essex County", ["East Ward", "complaints", "development", "transportation"]),
    ("New Jersey Civic Aspirants & Supporters Network", "Newark", "Essex County", ["elections", "candidate filings", "voter registration", "candidate forums"]),
]

SOURCES = [
    ("City of Newark", "Government", "https://www.newarknj.gov", None, 90),
    ("Essex County", "Government", "https://essexcountynj.org", None, 90),
    ("NJ Transit", "Transportation", "https://www.njtransit.com", "https://www.njtransit.com/rss/BusAdvisory.xml", 90),
    ("Newark Public Schools", "Schools", "https://www.nps.k12.nj.us", None, 90),
]


def _ensure_sqlite_columns(engine):
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as conn:
        tables = {row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}
        if "stories" not in tables:
            return
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(stories)"))}
        if "saved" not in cols:
            conn.execute(text("ALTER TABLE stories ADD COLUMN saved BOOLEAN DEFAULT 0"))


def initialize(engine):
    Base.metadata.create_all(engine)
    _ensure_sqlite_columns(engine)
    from sqlalchemy.orm import Session

    with Session(engine) as s:
        if not s.scalar(select(CommunityGroup.id).limit(1)):
            for name, city, county, topics in STARTERS:
                s.add(
                    CommunityGroup(
                        name=name,
                        city=city,
                        county=county,
                        state="New Jersey",
                        topics=[GroupTopic(name=x) for x in topics],
                    )
                )
        if not s.scalar(select(Source.id).limit(1)):
            for name, cat, url, rss, priority in SOURCES:
                s.add(
                    Source(
                        name=name,
                        category=cat,
                        website_url=url,
                        rss_url=rss,
                        priority=priority,
                    )
                )
        s.commit()
