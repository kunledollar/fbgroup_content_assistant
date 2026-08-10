"""Optional OpenAI-backed writer behind a safe local fallback boundary."""
from __future__ import annotations

import logging

from app.models.schemas import PostDraft
from app.services.writer import SafePostWriter

log = logging.getLogger(__name__)

SYSTEM = (
    "You draft careful Facebook community posts for local administrators. "
    "Never invent URLs, quotes, dates, or facts. Mark uncertain material clearly. "
    "Remain neutral on politics. Do not encourage harassment or private-data sharing. "
    "Keep sources in the body. Return plain text only."
)


class OpenAIPostWriter:
    def __init__(self, api_key: str | None, model: str = "gpt-4.1-mini"):
        self.api_key = api_key
        self.model = model
        self.fallback = SafePostWriter()

    def generate(self, story, group, variation="Standard", post_type="Community Update"):
        draft = self.fallback.generate(story, group, variation=variation, post_type=post_type)
        if not self.api_key:
            return draft
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            prompt = (
                f"Community: {group.name} ({group.city}, {group.state})\n"
                f"Tone: {getattr(group, 'tone', 'Community')}\n"
                f"Post type: {post_type}\nVariation: {variation}\n\n"
                f"Story title: {story.title}\n"
                f"Summary: {story.summary}\n"
                f"Source: {story.source}\nURL: {story.url}\n"
                f"Published: {story.published_at}\nReliability: {story.reliability}\n\n"
                "Improve the following draft without inventing facts:\n\n"
                f"{draft.body}"
            )
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )
            body = ((response.choices[0].message.content if response.choices else "") or "").strip()
            if not body:
                return draft
            warnings = list(draft.warnings)
            if story.reliability < 0.7 and "UNVERIFIED COMMUNITY REPORT" not in body:
                body = "UNVERIFIED COMMUNITY REPORT\n\n" + body
                warnings = ["UNVERIFIED COMMUNITY REPORT — confirm important claims before publishing."]
            if str(story.url) not in body:
                body += f"\n\nSource: {story.source} — {story.url}"
            return PostDraft(headline=story.title, body=body, warnings=warnings)
        except Exception:
            log.exception("OpenAI writer failed; using safe fallback")
            return draft


def build_writer(settings):
    return OpenAIPostWriter(settings.openai_api_key, settings.community_pulse_model)
