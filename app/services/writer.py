from app.models.schemas import PostDraft
class SafePostWriter:
    def generate(self, story, group, variation="Standard", post_type="Community Update"):
        date=story.published_at.strftime("%B %d, %Y") if story.published_at else "Publication date not provided"
        event=story.event_at.strftime("%B %d, %Y at %I:%M %p") if story.event_at else None
        warning=[]
        if story.reliability < .7: warning=["UNVERIFIED COMMUNITY REPORT — confirm important claims before publishing."]
        label="UNVERIFIED COMMUNITY REPORT\n\n" if warning else ""
        detail=story.summary.strip() or "The source has not provided a summary. Open it and verify the details before posting."
        body=f"{label}📍 {group.city.upper()} COMMUNITY UPDATE\n\n{story.title}\n\n{detail}\n\nARTICLE PUBLISHED: {date}"
        if event: body+=f"\nEVENT DATE: {event}"
        body+=f"\n\nWHY IT MATTERS:\nThis may affect residents in {group.city}. Review the source for complete details.\n\n💬 What questions or firsthand experiences should the community add?\n\nSource: {story.source} — {story.url}"
        if variation=="Short": body="\n\n".join(body.split("\n\n")[:3])+f"\n\nSource: {story.url}"
        return PostDraft(headline=story.title,body=body,warnings=warning)
