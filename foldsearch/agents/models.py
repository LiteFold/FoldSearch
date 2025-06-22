from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

# ===== WEB RESEARCH MODELS =====

class SearchResult(BaseModel):
    title: str
    url: str
    abstract: str

class WebResearchResult(BaseModel):
    search_result: list[SearchResult]

class UpNextQueries(BaseModel):
    queries: list[str]

class WebResearchAgentModel(BaseModel):
    query: str
    raw_result: str
    research_paper: WebResearchResult
    upnext_queries: list[str]

# ===== PROTEIN SEARCH MODELS =====

class ToolsToUseResult(BaseModel):
    tools_to_use: list[str]

# Import specific models from protein_search module
try:
    from agents.protein_search.models import ProteinSearchResponse
except ImportError:
    # Handle circular import by defining a placeholder
    ProteinSearchResponse = Any

# ===== UNIFIED AGENT MODELS =====

class CombinedSearchResult(BaseModel):
    """
    Combined result model that returns separate results by tool name
    """
    query: str
    
    # Tool-specific results dictionary - tool_name: tool_result
    tool_results: Dict[str, Any] = {}
    
    # Combined metadata
    search_type: str  # 'web', 'protein', or 'combined'
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True
    error_message: str = ""
    
    # Summary statistics
    total_tools_used: int = 0
    successful_tools: int = 0
    failed_tools: int = 0
    total_execution_time: float = 0.0
    
    class Config:
        extra = "allow"
    
    def has_web_results(self) -> bool:
        """Check if there are web research results"""
        return "web_search_tool" in self.tool_results and self.tool_results["web_search_tool"] is not None
    
    def has_protein_results(self) -> bool:
        """Check if there are protein search results"""
        protein_tools = [k for k in self.tool_results.keys() if k != "web_search_tool"]
        return len(protein_tools) > 0 and any(self.tool_results[k] for k in protein_tools)
    
    def get_summary(self) -> str:
        """Get a summary of all results"""
        summaries = []
        
        if self.has_web_results():
            web_result = self.tool_results.get("web_search_tool", {})
            if isinstance(web_result, dict) and "research_paper" in web_result:
                web_count = len(web_result["research_paper"].get("search_result", []))
                summaries.append(f"{web_count} web results")
        
        if self.has_protein_results():
            protein_tools = [k for k in self.tool_results.keys() if k != "web_search_tool"]
            total_structures = set()
            for tool_name in protein_tools:
                tool_result = self.tool_results.get(tool_name)
                if tool_result and hasattr(tool_result, 'pdb_ids'):
                    total_structures.update(tool_result.pdb_ids)
            summaries.append(f"Protein: {len(protein_tools)} tools used, {len(total_structures)} unique structures found")
        
        if not summaries:
            return "No results found"
        
        return "; ".join(summaries)
