from typing import TypedDict, List
from schemas import Source, Fact

class MarketAnalysisState(TypedDict):
    topic: str
    search_queries: List[str]
    sources: List[Source]
    key_facts: List[Fact]
    final_analysis: str
