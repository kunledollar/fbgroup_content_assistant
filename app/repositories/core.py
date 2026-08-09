from sqlalchemy import select
from app.models.entities import CommunityGroup, GeneratedPost, Source
class GroupRepository:
    def __init__(self, session): self.s=session
    def all(self): return list(self.s.scalars(select(CommunityGroup).order_by(CommunityGroup.name)))
    def add(self, group): self.s.add(group); self.s.commit(); return group
    def delete(self, group): self.s.delete(group); self.s.commit()
class SourceRepository:
    def __init__(self, session): self.s=session
    def all(self): return list(self.s.scalars(select(Source).order_by(Source.priority.desc())))
class PostRepository:
    def __init__(self, session): self.s=session
    def save(self, post): self.s.add(post); self.s.commit(); return post
    def all(self): return list(self.s.scalars(select(GeneratedPost).order_by(GeneratedPost.created_at.desc())))
