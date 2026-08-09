from datetime import datetime
from app.agents.core import QueryPlanner, RelevanceAgent, FreshnessAgent, DeduplicationAgent, ReliabilityAgent, RankingAgent
class ResearchOrchestrator:
    def __init__(self, provider):
        self.provider=provider; self.planner=QueryPlanner(); self.relevance=RelevanceAgent(); self.freshness=FreshnessAgent(); self.dedupe=DeduplicationAgent(); self.reliability=ReliabilityAgent(); self.ranking=RankingAgent()
    async def run(self, group, since: datetime | None=None, topic=""):
        results=[]
        for query in self.planner.plan(group,topic): results.extend(await self.provider.search(query,since))
        ranked=[]
        for item in self.dedupe.deduplicate(results):
            local=self.relevance.score(item,group)
            if local < .25: continue
            item.local_relevance=local; rel=self.reliability.score(item); item.reliability=rel
            score,reason=self.ranking.rank(item,self.freshness.score(item.published_at),local,rel)
            ranked.append((score,reason,item))
        return sorted(ranked,key=lambda x:x[0],reverse=True)
