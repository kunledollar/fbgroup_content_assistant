"""Image suggestion boundary — never downloads copyrighted news photographs."""
from pydantic import BaseModel


class ImageSuggestion(BaseModel):
    title: str
    license: str
    attribution: str
    source_url: str | None = None
    note: str


class ImageProvider:
    def suggest(self, story, group) -> ImageSuggestion:
        host = str(getattr(story, "url", "") or "")
        official = any(
            marker in host
            for marker in (".gov", "nj.gov", "newarknj.gov", "njtransit.com", "nps.k12.nj.us")
        )
        if official:
            return ImageSuggestion(
                title="Official public source graphic (manual selection)",
                license="Verify agency reuse terms before posting",
                attribution=getattr(story, "source", "Official source"),
                source_url=str(story.url) if getattr(story, "url", None) else None,
                note=(
                    "Prefer maps, flyers, or graphics published by the agency for reuse. "
                    "Do not scrape or download news photographs."
                ),
            )
        return ImageSuggestion(
            title="No automatic image selected",
            license="Not selected",
            attribution="",
            source_url=None,
            note=(
                "Copyrighted news images are never downloaded. "
                "Use only official, public-domain, or explicitly licensed media and keep attribution."
            ),
        )
