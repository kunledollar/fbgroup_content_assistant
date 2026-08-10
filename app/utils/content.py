import re
from datetime import datetime

from bs4 import BeautifulSoup
from dateutil import parser


def sanitize_pasted(value: str) -> str:
    soup=BeautifulSoup(value,"html.parser")
    for tag in soup(["script","style","iframe","object"]):tag.decompose()
    return re.sub(r"\n{3,}","\n\n",soup.get_text("\n")).strip()

def extract_date(value: str) -> datetime | None:
    patterns=[r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b",r"\b\d{4}-\d{2}-\d{2}\b"]
    for pattern in patterns:
        hit=re.search(pattern,value,re.IGNORECASE)
        if hit:
            try:return parser.parse(hit.group(0),fuzzy=False)
            except ValueError:pass
    return None

def topic_match(text: str, topics: list[str]) -> float:
    lowered=text.lower();return sum(t.lower() in lowered for t in topics)/max(1,len(topics))
