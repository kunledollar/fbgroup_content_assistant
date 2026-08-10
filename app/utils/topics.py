"""Map free-text stories into newsroom navigation topics."""

TOPIC_KEYWORDS = {
    "Events": ("event", "festival", "hearing", "forum", "ceremony", "parade"),
    "Government": ("government", "council", "mayor", "ordinance", "municipal", "city hall"),
    "Politics & Elections": ("election", "candidate", "voter", "ballot", "primary", "campaign"),
    "Schools & Parents": ("school", "student", "teacher", "board of education", "parents", "nps"),
    "Transportation": ("transit", "bus", "train", "traffic", "road closure", "path", "parking"),
    "Housing": ("housing", "tenant", "rent", "eviction", "landlord", "affordable"),
    "Public Safety": ("police", "fire", "safety", "crime", "emergency", "alert"),
    "Community Activities": ("community", "volunteer", "program", "recreation", "neighborhood"),
    "Projects & Development": ("development", "construction", "zoning", "project", "redevelopment"),
    "Complaints & Civic Issues": ("complaint", "pothole", "code enforcement", "trash", "noise"),
}


def classify_topic(title: str, summary: str = "", fallback: str = "Community") -> str:
    text = f"{title} {summary}".lower()
    best, hits = fallback, 0
    for topic, words in TOPIC_KEYWORDS.items():
        count = sum(1 for w in words if w in text)
        if count > hits:
            best, hits = topic, count
    return best
