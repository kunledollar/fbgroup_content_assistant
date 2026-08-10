from sqlalchemy import select

from app.models.entities import CommunityGroup, GeneratedPost, Source, Story


class GroupRepository:
    def __init__(self, session):
        self.s = session

    def all(self):
        return list(self.s.scalars(select(CommunityGroup).order_by(CommunityGroup.name)))

    def add(self, group):
        self.s.add(group)
        self.s.commit()
        return group

    def delete(self, group):
        self.s.delete(group)
        self.s.commit()


class SourceRepository:
    def __init__(self, session):
        self.s = session

    def all(self):
        return list(self.s.scalars(select(Source).order_by(Source.priority.desc(), Source.name)))

    def enabled_rss_urls(self):
        return [
            x.rss_url
            for x in self.all()
            if x.enabled and x.rss_url
        ]

    def add(self, source):
        self.s.add(source)
        self.s.commit()
        return source

    def delete(self, source):
        self.s.delete(source)
        self.s.commit()

    def save(self):
        self.s.commit()


class StoryRepository:
    def __init__(self, session):
        self.s = session

    def all(self):
        return list(self.s.scalars(select(Story).order_by(Story.score.desc(), Story.id.desc())))

    def by_topic(self, topic: str):
        return list(
            self.s.scalars(
                select(Story)
                .where(Story.topic == topic)
                .order_by(Story.score.desc(), Story.id.desc())
            )
        )

    def saved(self):
        return list(
            self.s.scalars(
                select(Story).where(Story.saved.is_(True)).order_by(Story.score.desc(), Story.id.desc())
            )
        )

    def upsert_from_result(self, result, score: float, reason: str, topic: str = "Community"):
        existing = self.s.scalar(select(Story).where(Story.url == str(result.url)))
        confidence = "Verified" if result.reliability >= 0.7 else "Unverified"
        if existing:
            existing.title = result.title
            existing.summary = result.summary
            existing.source_name = result.source
            existing.published_at = result.published_at
            existing.event_at = result.event_at
            existing.location = result.location or existing.location
            existing.topic = topic or existing.topic
            existing.score = score
            existing.score_reason = reason
            existing.confidence = confidence
            self.s.commit()
            return existing
        story = Story(
            title=result.title,
            summary=result.summary,
            url=str(result.url),
            source_name=result.source,
            published_at=result.published_at,
            event_at=result.event_at,
            location=result.location or "",
            topic=topic,
            score=score,
            score_reason=reason,
            confidence=confidence,
        )
        self.s.add(story)
        self.s.commit()
        return story

    def set_saved(self, story, saved: bool = True):
        story.saved = saved
        self.s.commit()
        return story

    def delete(self, story):
        self.s.delete(story)
        self.s.commit()


class PostRepository:
    def __init__(self, session):
        self.s = session

    def save(self, post):
        self.s.add(post)
        self.s.commit()
        return post

    def all(self):
        return list(self.s.scalars(select(GeneratedPost).order_by(GeneratedPost.created_at.desc())))

    def get(self, post_id: int):
        return self.s.get(GeneratedPost, post_id)

    def delete(self, post):
        self.s.delete(post)
        self.s.commit()
