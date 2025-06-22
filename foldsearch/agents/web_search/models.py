from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    abstract: str

class WebResearchResult(BaseModel):
    search_result: list[SearchResult]

class UpNextQueries(BaseModel):
    queries: list[str]

from typing import Optional, Any

class WebResearchAgentModel(BaseModel):
    query: str
    raw_result: str
    research_paper: WebResearchResult
    upnext_queries: list[str]
    biological_analysis: Optional[Any] = None  # BiologicalAnalysis type