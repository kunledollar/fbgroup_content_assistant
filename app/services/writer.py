from app.models.schemas import PostDraft, SearchResult
from app.utils.content import sanitize_pasted


class SafePostWriter:
    def generate(self, story, group, variation="Standard", post_type="Community Update"):
        date = story.published_at.strftime("%B %d, %Y") if story.published_at else "Publication date not provided"
        event = story.event_at.strftime("%B %d, %Y at %I:%M %p") if story.event_at else None
        warning = []
        if getattr(story, "reliability", 0.5) < 0.7:
            warning = ["UNVERIFIED COMMUNITY REPORT — confirm important claims before publishing."]
        label = "UNVERIFIED COMMUNITY REPORT\n\n" if warning else ""
        detail = (story.summary or "").strip() or (
            "The source has not provided a summary. Open it and verify the details before posting."
        )
        body = (
            f"{label}📍 {group.city.upper()} COMMUNITY UPDATE\n\n"
            f"{story.title}\n\n{detail}\n\nARTICLE PUBLISHED: {date}"
        )
        if event:
            body += f"\nEVENT DATE: {event}"
        body += (
            f"\n\nWHY IT MATTERS:\nThis may affect residents in {group.city}. "
            f"Review the source for complete details.\n\n"
            f"💬 What questions or firsthand experiences should the community add?\n\n"
            f"Source: {story.source} — {story.url}"
        )
        if variation == "Short":
            body = "\n\n".join(body.split("\n\n")[:3]) + f"\n\nSource: {story.url}"
        return PostDraft(headline=story.title, body=body, warnings=warning)

    def from_paste(self, text: str, group) -> PostDraft:
        clean = sanitize_pasted(text)
        if not clean:
            return PostDraft(headline="", body="", warnings=["Nothing to draft."])
        headline = clean.splitlines()[0][:150]
        body = (
            "UNVERIFIED COMMUNITY REPORT\n\n"
            "📍 COMMUNITY QUESTION\n\n"
            f"{headline}\n\n"
            "Several residents or sources have raised the following information:\n\n"
            f"{clean}\n\n"
            "This information has not yet been independently verified. "
            "Please share firsthand details or an official source without identifying private individuals.\n\n"
            "💬 What have you observed, and which public agency should follow up?"
        )
        return PostDraft(
            headline=headline,
            body=body,
            warnings=["UNVERIFIED COMMUNITY REPORT — confirm important claims before publishing."],
        )

    def story_from_paste(self, text: str) -> SearchResult:
        clean = sanitize_pasted(text)
        headline = (clean.splitlines()[0] if clean else "Resident report")[:150]
        return SearchResult(
            title=headline,
            url="https://example.org/local-report",
            summary=clean,
            source="Resident / pasted information",
            reliability=0.35,
        )
