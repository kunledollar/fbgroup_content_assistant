from sqlalchemy.orm import Session
from app.database.session import make_engine,Base
from app.database.bootstrap import initialize
from app.models.entities import CommunityGroup,GroupTopic
from app.models.schemas import SearchResult
from app.services.writer import SafePostWriter

def test_starter_groups_and_editable_crud():
    e=make_engine("sqlite://");initialize(e)
    with Session(e) as s:
        assert s.query(CommunityGroup).count()==10
        g=CommunityGroup(name="Test",city="Bloomfield",county="Essex",state="New Jersey",topics=[GroupTopic(name="parks")]);s.add(g);s.commit();g.city="Belleville";s.commit();assert s.get(CommunityGroup,g.id).city=="Belleville";s.delete(g);s.commit()
def test_post_generation_marks_unverified():
    story=SearchResult(title="Resident report",url="https://example.org/report",source="Resident",summary="A concern was submitted",reliability=.4)
    group=CommunityGroup(name="Community",city="Newark",county="Essex",state="New Jersey")
    draft=SafePostWriter().generate(story,group);assert "UNVERIFIED COMMUNITY REPORT" in draft.body;assert str(story.url) in draft.body
