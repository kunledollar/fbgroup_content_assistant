import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from app.models.schemas import SearchResult

OFFICIAL_MARKERS=(".gov","nj.gov","newarknj.gov","nps.k12.nj.us","njtransit.com","panynj.gov")
class QueryPlanner:
    def plan(self, group, topic="", max_queries=4):
        place=" ".join(filter(None,[group.city,group.county,group.state]))
        topics=[x.name for x in group.topics][:3] or [topic or "community news"]
        return [f'"{group.city}" {t} {topic}'.strip() for t in topics][:max_queries] + [f'"{place}" public notice {topic}'.strip()]

class RelevanceAgent:
    def score(self, result: SearchResult, group) -> float:
        text=f"{result.title} {result.summary} {result.location}".lower()
        if any(x.strip().lower() in text for x in group.excluded_keywords.split(",") if x.strip()): return 0
        city=group.city.lower(); state=group.state.lower()
        if city == "newark" and any(x in text for x in ("california","delaware","ohio")): return 0
        hits=sum(token in text for token in [city,state,"new jersey",group.county.lower()] if token)
        topic_hits=sum(t.name.lower() in text for t in group.topics)
        return min(1.0, .35*hits + .15*topic_hits)

class FreshnessAgent:
    def score(self, published, now=None):
        if not published: return .15
        now=now or datetime.now(timezone.utc); published=published if published.tzinfo else published.replace(tzinfo=timezone.utc)
        hours=max(0,(now-published).total_seconds()/3600)
        return 1 if hours<=24 else .85 if hours<=72 else .65 if hours<=168 else .4 if hours<=720 else .1

class DeduplicationAgent:
    def deduplicate(self, results):
        kept=[]
        for item in results:
            normalized=re.sub(r"\W+"," ",item.title.lower())
            if not any(SequenceMatcher(None,normalized,re.sub(r"\W+"," ",x.title.lower())).ratio()>.82 for x in kept): kept.append(item)
        return kept

class ReliabilityAgent:
    def score(self, result):
        host=str(result.url).lower()
        return .95 if any(x in host for x in OFFICIAL_MARKERS) else .75 if result.reliability>=.7 else .5

class RankingAgent:
    weights={"freshness":.25,"local":.25,"impact":.20,"discussion":.15,"actionability":.10,"source":.05}
    def rank(self,result,freshness,local,reliability):
        impact=.7 if any(x in result.title.lower() for x in ("meeting","closure","election","school","safety","housing")) else .5
        discussion=.65; action=.75 if result.event_at or any(x in result.summary.lower() for x in ("register","attend","deadline")) else .45
        parts={"freshness":freshness,"local":local,"impact":impact,"discussion":discussion,"actionability":action,"source":reliability}
        score=round(sum(parts[k]*self.weights[k] for k in parts)*100,1)
        return score, "; ".join(f"{k} {round(v*100)}%" for k,v in parts.items())
