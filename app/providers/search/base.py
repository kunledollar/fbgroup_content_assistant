from abc import ABC, abstractmethod
from datetime import datetime
from app.models.schemas import SearchResult
class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, since: datetime | None = None, limit: int = 20) -> list[SearchResult]: ...
