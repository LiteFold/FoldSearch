from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import time
from datetime import datetime

from agents.web_search.worker import WebResearchAgent
from agents.protein_search.worker import ProteinSearchAgent
from agents.models import CombinedSearchResult
from agents.web_search.models import WebResearchAgentModel
from agents.protein_search.models import ProteinSearchUnifiedResults
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FoldSearch API",
    description="Combined web research and protein structure search API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


web_agent = None
protein_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    global web_agent, protein_agent
    print("🚀 Initializing FoldSearch API...")
    web_agent = WebResearchAgent()
    protein_agent = ProteinSearchAgent()
    print("✅ Agents initialized successfully!")

class SearchRequest(BaseModel):
    query: str
    include_web: bool = True
    include_protein: bool = True
    max_protein_queries: int = 5

class SearchResponse(BaseModel):
    success: bool
    message: str
    data: Optional[CombinedSearchResult] = None
    execution_time: float
    timestamp: datetime

def deduplicate_protein_results(protein_results: List[ProteinSearchUnifiedResults]) -> Optional[ProteinSearchUnifiedResults]:
    """
    De-duplicate and merge multiple protein search results
    """
    if not protein_results:
        print("   No protein results to deduplicate")
        return None
    
    print(f"   Deduplicating {len(protein_results)} protein search results...")
    
    if len(protein_results) == 1:
        print(f"   Single result with {protein_results[0].get_result_count()} items")
        return protein_results[0]
    
    # Combine all results into one unified result
    combined = ProteinSearchUnifiedResults(
        operation_type="combined_protein_search",
        timestamp=datetime.now(),
        success=True,
        query_params={"combined_queries": len(protein_results)}
    )
    
    # Track data for deduplication
    all_pdb_ids = set()
    all_scores = {}
    all_tools = set()
    all_errors = []
    total_execution_time = 0.0
    successful_retrievals = 0
    failed_retrievals = 0
    
    # Aggregate data from all results
    for i, result in enumerate(protein_results):
        print(f"   Processing result {i+1}: success={result.success}, pdb_count={result.get_result_count()}")
        
        if result.success:
            successful_retrievals += 1
            
            # Collect PDB IDs (deduplicated via set)
            if result.pdb_ids:
                print(f"     Adding {len(result.pdb_ids)} PDB IDs")
                all_pdb_ids.update(result.pdb_ids)
            
            # Collect scores
            if result.scores:
                all_scores.update(result.scores)
            
            # Collect tools used
            if result.tool_used:
                all_tools.add(result.tool_used)
            
            # Sum execution times
            if result.execution_time:
                total_execution_time += result.execution_time
        else:
            failed_retrievals += 1
            if result.error_message:
                all_errors.append(result.error_message)
    
    # Set combined fields
    combined.pdb_ids = list(all_pdb_ids) if all_pdb_ids else []
    combined.scores = all_scores if all_scores else {}
    combined.total_count = len(all_pdb_ids)
    combined.returned_count = len(all_pdb_ids)
    combined.tool_used = ", ".join(sorted(all_tools)) if all_tools else None
    combined.execution_time = total_execution_time
    combined.successful_retrievals = successful_retrievals
    combined.failed_retrievals = failed_retrievals
    combined.warnings = all_errors if all_errors else None
    combined.success = successful_retrievals > 0
    
    # Store original results for reference
    combined.raw_response = {
        "original_results_count": len(protein_results),
        "deduplicated_pdb_count": len(all_pdb_ids),
        "individual_counts": [r.get_result_count() for r in protein_results]
    }
    
    print(f"   Deduplication complete: {len(all_pdb_ids)} unique PDB IDs from {len(protein_results)} searches")
    
    return combined

async def run_web_search(query: str) -> Optional[WebResearchAgentModel]:
    """Run web search in a separate thread"""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, web_agent.search, query)
        return result
    except Exception as e:
        print(f"❌ Web search error: {e}")
        return None

async def run_protein_search(query: str) -> Optional[ProteinSearchUnifiedResults]:
    """Run protein search in a separate thread"""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, protein_agent.search, query)
        return result
    except Exception as e:
        print(f"❌ Protein search error: {e}")
        return None

@app.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """
    Main search endpoint that combines web research and protein structure search
    
    Args:
        request: SearchRequest containing query and search options
    
    Returns:
        SearchResponse with combined and deduplicated results
    """
    start_time = time.time()
    
    try:
        print(f"🔍 Processing search request: {request.query}")
        print(f"   - Include web: {request.include_web}")
        print(f"   - Include protein: {request.include_protein}")
        
        # Initialize tasks list
        tasks = []
        web_result = None
        protein_results = []
        
        # Phase 1: Run web search if requested
        if request.include_web:
            print("🖥️  Starting web search...")
            web_task = run_web_search(request.query)
            web_result = await web_task
        
        # Phase 2: Run protein searches if requested
        if request.include_protein:
            if web_result and web_result.upnext_queries:
                # Use follow-up queries from web search for protein search
                protein_queries = web_result.upnext_queries[:request.max_protein_queries]
                print(f"🧬 Running protein searches for {len(protein_queries)} queries...")
                
                # Run protein searches in parallel
                protein_tasks = [run_protein_search(query) for query in protein_queries]
                protein_results = await asyncio.gather(*protein_tasks, return_exceptions=True)
                
                # Filter out exceptions and None results
                protein_results = [r for r in protein_results if isinstance(r, ProteinSearchUnifiedResults) and r is not None]
            else:
                # Fallback: run protein search with original query
                print("🧬 Running protein search with original query...")
                protein_result = await run_protein_search(request.query)
                if protein_result:
                    protein_results = [protein_result]
        
        # Phase 3: Aggregate and deduplicate results
        print("📊 Aggregating and deduplicating results...")
        
        # Deduplicate protein results
        combined_protein_result = deduplicate_protein_results(protein_results) if protein_results else None
        
        # Determine search type
        search_type = "combined" if (web_result and combined_protein_result) else \
                     "web" if web_result else \
                     "protein" if combined_protein_result else \
                     "none"
        
        # Create combined result - convert models to dicts to avoid validation issues
        web_research_dict = web_result.dict() if web_result else None
        protein_search_dict = combined_protein_result.dict() if combined_protein_result else None
        
        combined_result = CombinedSearchResult(
            query=request.query,
            web_research=web_research_dict,
            protein_search=protein_search_dict,
            search_type=search_type,
            timestamp=datetime.now(),
            success=bool(web_result or combined_protein_result)
        )
        
        execution_time = time.time() - start_time
        
        # Generate summary message
        summary = combined_result.get_summary()
        message = f"Search completed successfully. {summary}"
        
        print(f"✅ Search completed in {execution_time:.2f}s")
        print(f"   - {summary}")
        
        return SearchResponse(
            success=True,
            message=message,
            data=combined_result,
            execution_time=execution_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_message = f"Search failed: {str(e)}"
        print(f"❌ {error_message}")
        
        return SearchResponse(
            success=False,
            message=error_message,
            data=None,
            execution_time=execution_time,
            timestamp=datetime.now()
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "FoldSearch API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/search - Main search endpoint (POST)",
            "health": "/health - Health check (GET)",
            "docs": "/docs - API documentation (GET)"
        }
    }

# Example usage for testing
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FoldSearch API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
