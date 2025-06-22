from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import time
from datetime import datetime

from agents.web_search.worker import WebResearchAgent
from agents.protein_search.worker import ProteinSearchAgent
from agents.models import CombinedSearchResult
from agents.protein_search.models import ProteinSearchResponse
from agents.web_search.models import WebResearchAgentModel
from agents.analysis_service import AnalysisService
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
analysis_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    global web_agent, protein_agent, analysis_service
    print("🚀 Initializing FoldSearch API...")
    web_agent = WebResearchAgent()
    protein_agent = ProteinSearchAgent()
    analysis_service = AnalysisService()
    print("✅ Agents and analysis service initialized successfully!")

class SearchRequest(BaseModel):
    query: str
    include_web: bool = True
    include_protein: bool = True
    max_protein_queries: int = 5
    include_analysis: bool = True

class WebSearchRequest(BaseModel):
    query: str
    include_analysis: bool = True

class ProteinSearchRequest(BaseModel):
    query: str
    include_analysis: bool = True

class SearchResponse(BaseModel):
    success: bool
    message: str
    data: Optional[CombinedSearchResult] = None
    execution_time: float
    timestamp: datetime

class WebSearchResponse(BaseModel):
    success: bool
    message: str
    data: Optional[WebResearchAgentModel] = None
    execution_time: float
    timestamp: datetime

class ProteinOnlySearchResponse(BaseModel):
    success: bool
    message: str
    data: Optional[ProteinSearchResponse] = None
    execution_time: float
    timestamp: datetime

async def run_web_search(query: str) -> Optional[WebResearchAgentModel]:
    """Run web search in a separate thread"""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, web_agent.search, query)
        return result
    except Exception as e:
        print(f"❌ Web search error: {e}")
        return None

async def run_protein_search(query: str) -> Optional[ProteinSearchResponse]:
    """Run protein search in a separate thread"""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, protein_agent.search, query)
        return result
    except Exception as e:
        print(f"❌ Protein search error: {e}")
        return None


@app.post("/web-search", response_model=WebSearchResponse)
async def web_search_endpoint(request: WebSearchRequest):
    """
    Web-only search endpoint that performs web research
    
    Args:
        request: WebSearchRequest containing query
    
    Returns:
        WebSearchResponse with web search results
    """
    start_time = time.time()
    
    try:
        print(f"🔍 Processing web search request: {request.query}")
        
        # Run web search
        web_result = await run_web_search(request.query)
        
        # Generate analysis if requested
        if request.include_analysis and web_result:
            print("🧠 Generating biological analysis...")
            try:
                # Prepare data for analysis
                analysis_data = {"web_search_tool": web_result.dict()}
                analysis = await analysis_service.generate_analysis(
                    query=request.query,
                    search_results=analysis_data,
                    analysis_type="web"
                )
                web_result.biological_analysis = analysis
                print(f"✅ Analysis completed in {analysis.processing_time:.2f}s")
            except Exception as e:
                print(f"⚠️  Analysis failed: {e}")
        
        execution_time = time.time() - start_time
        
        if web_result:
            print(f"✅ Web search completed successfully in {execution_time:.2f}s")
            results_count = len(web_result.research_paper.search_result) if web_result.research_paper and web_result.research_paper.search_result else 0
            analysis_note = " with biological analysis" if request.include_analysis and web_result.biological_analysis else ""
            return WebSearchResponse(
                success=True,
                message=f"Web search completed successfully{analysis_note}. Found {results_count} results.",
                data=web_result,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
        else:
            print(f"❌ Web search failed in {execution_time:.2f}s")
            return WebSearchResponse(
                success=False,
                message="Web search failed",
                data=None,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
    except Exception as e:
        execution_time = time.time() - start_time
        error_message = f"Web search failed: {str(e)}"
        print(f"❌ {error_message}")
        
        return WebSearchResponse(
            success=False,
            message=error_message,
            data=None,
            execution_time=execution_time,
            timestamp=datetime.now()
        )


@app.post("/protein-search", response_model=ProteinOnlySearchResponse)
async def protein_search_endpoint(request: ProteinSearchRequest):
    """
    Protein-only search endpoint that performs protein structure search
    
    Args:
        request: ProteinSearchRequest containing query
    
    Returns:
        ProteinOnlySearchResponse with protein search results
    """
    start_time = time.time()
    
    try:
        print(f"🔍 Processing protein search request: {request.query}")
        
        # Run protein search
        protein_result = await run_protein_search(request.query)
        
        # Generate analysis if requested
        if request.include_analysis and protein_result and protein_result.success:
            print("🧠 Generating biological analysis...")
            try:
                # Prepare data for analysis
                analysis_data = {}
                for tool_result in protein_result.tool_results:
                    analysis_data[tool_result.tool_name] = tool_result
                
                analysis = await analysis_service.generate_analysis(
                    query=request.query,
                    search_results=analysis_data,
                    analysis_type="protein"
                )
                protein_result.biological_analysis = analysis
                print(f"✅ Analysis completed in {analysis.processing_time:.2f}s")
            except Exception as e:
                print(f"⚠️  Analysis failed: {e}")
        
        execution_time = time.time() - start_time
        
        if protein_result and protein_result.success:
            print(f"✅ Protein search completed successfully in {execution_time:.2f}s")
            total_results = sum(len(tool.data) if hasattr(tool, 'data') and tool.data else 0 
                              for tool in protein_result.tool_results if tool.success)
            analysis_note = " with biological analysis" if request.include_analysis and protein_result.biological_analysis else ""
            return ProteinOnlySearchResponse(
                success=True,
                message=f"Protein search completed successfully{analysis_note}. Found results from {len(protein_result.tool_results)} tools with {total_results} total entries.",
                data=protein_result,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
        else:
            print(f"❌ Protein search failed in {execution_time:.2f}s")
            return ProteinOnlySearchResponse(
                success=False,
                message="Protein search failed or returned no results",
                data=protein_result,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
    except Exception as e:
        execution_time = time.time() - start_time
        error_message = f"Protein search failed: {str(e)}"
        print(f"❌ {error_message}")
        
        return ProteinOnlySearchResponse(
            success=False,
            message=error_message,
            data=None,
            execution_time=execution_time,
            timestamp=datetime.now()
        )


@app.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """
    Main search endpoint that combines web research and protein structure search
    Returns separate results for each tool used
    
    Args:
        request: SearchRequest containing query and search options
    
    Returns:
        SearchResponse with tool-specific results
    """
    start_time = time.time()
    
    try:
        print(f"🔍 Processing search request: {request.query}")
        print(f"   - Include web: {request.include_web}")
        print(f"   - Include protein: {request.include_protein}")
        
        # Initialize tool results dictionary
        tool_results = {}
        total_tools_used = 0
        successful_tools = 0
        failed_tools = 0
        
        # Phase 1: Run web search if requested
        if request.include_web:
            print("🖥️  Starting web search...")
            web_result = await run_web_search(request.query)
            total_tools_used += 1
            
            if web_result:
                tool_results["web_search_tool"] = web_result.dict()
                successful_tools += 1
                print("✅ Web search completed successfully")
            else:
                tool_results["web_search_tool"] = {
                    "query": request.query,
                    "success": False,
                    "error": "Web search failed"
                }
                failed_tools += 1
                print("❌ Web search failed")
        
        # Phase 2: Run protein search if requested
        if request.include_protein:
            protein_queries = []
            
            # Determine protein search queries
            if request.include_web and web_result and web_result.upnext_queries:
                # Use follow-up queries from web search for protein search
                protein_queries = web_result.upnext_queries[:request.max_protein_queries]
                print(f"🧬 Running protein searches for {len(protein_queries)} queries...")
            else:
                # Fallback: run protein search with original query
                protein_queries = [request.query]
                print("🧬 Running protein search with original query...")
            
            # Run protein searches in parallel
            protein_tasks = [run_protein_search(query) for query in protein_queries]
            protein_results = await asyncio.gather(*protein_tasks, return_exceptions=True)
            
            # Process each protein search result separately
            for i, result in enumerate(protein_results):
                query_used = protein_queries[i]
                
                if isinstance(result, ProteinSearchResponse) and result is not None:
                    # Each tool result gets added separately
                    for tool_result in result.tool_results:
                        tool_name = tool_result.tool_name
                        # Add query suffix if multiple queries were used
                        if len(protein_queries) > 1:
                            unique_tool_name = f"{tool_name}_query_{i+1}"
                        else:
                            unique_tool_name = tool_name
                        
                        tool_results[unique_tool_name] = tool_result
                        total_tools_used += 1
                        
                        if tool_result.success:
                            successful_tools += 1
                        else:
                            failed_tools += 1
                else:
                    # Handle failed protein search
                    tool_results[f"protein_search_query_{i+1}"] = {
                        "query": query_used,
                        "success": False,
                        "error": str(result) if isinstance(result, Exception) else "Protein search failed"
                    }
                    total_tools_used += 1
                    failed_tools += 1
        
        # Phase 3: Generate analysis if requested
        if request.include_analysis and successful_tools > 0:
            print("🧠 Generating comprehensive biological analysis...")
            try:
                # Determine analysis type
                has_web = "web_search_tool" in tool_results
                has_protein = any(k != "web_search_tool" for k in tool_results.keys())
                
                analysis_type = "combined" if (has_web and has_protein) else \
                               "web" if has_web else \
                               "protein" if has_protein else \
                               "none"
                
                analysis = await analysis_service.generate_analysis(
                    query=request.query,
                    search_results=tool_results,
                    analysis_type=analysis_type
                )
                print(f"✅ Analysis completed in {analysis.processing_time:.2f}s")
            except Exception as e:
                print(f"⚠️  Analysis failed: {e}")
                analysis = None
        else:
            analysis = None
        
        # Phase 4: Create combined result with tool-specific results
        print("📊 Creating tool-specific result...")
        
        # Determine search type
        has_web = "web_search_tool" in tool_results
        has_protein = any(k != "web_search_tool" for k in tool_results.keys())
        
        search_type = "combined" if (has_web and has_protein) else \
                     "web" if has_web else \
                     "protein" if has_protein else \
                     "none"
        
        # Create combined result with tool-specific format
        combined_result = CombinedSearchResult(
            query=request.query,
            tool_results=tool_results,
            biological_analysis=analysis,
            search_type=search_type,
            timestamp=datetime.now(),
            success=successful_tools > 0,
            total_tools_used=total_tools_used,
            successful_tools=successful_tools,
            failed_tools=failed_tools,
            total_execution_time=time.time() - start_time
        )
        
        execution_time = time.time() - start_time
        
        # Generate summary message
        summary = combined_result.get_summary()
        analysis_note = " with comprehensive biological analysis" if request.include_analysis and analysis else ""
        message = f"Search completed successfully{analysis_note}. {summary}"
        
        print(f"✅ Search completed in {execution_time:.2f}s")
        print(f"   - {summary}")
        print(f"   - Tools used: {total_tools_used}")
        print(f"   - Successful: {successful_tools}")
        print(f"   - Failed: {failed_tools}")
        
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
            data=CombinedSearchResult(
                query=request.query,
                search_type="none",
                success=False,
                error_message=str(e)
            ),
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
        "message": "FoldSearch API with GPT-4o Biological Analysis",
        "version": "1.0.0",
        "features": [
            "Web research and protein structure search",
            "GPT-4o powered biological analysis",
            "Scientific recommendations and insights",
            "Comprehensive data integration"
        ],
        "endpoints": {
            "search": "/search - Combined search endpoint with analysis (POST)",
            "web-search": "/web-search - Web-only search endpoint with analysis (POST)",
            "protein-search": "/protein-search - Protein-only search endpoint with analysis (POST)",
            "health": "/health - Health check (GET)",
            "docs": "/docs - API documentation (GET)"
        },
        "analysis_features": {
            "scientific_summary": "Concise overview of findings",
            "key_findings": "Most important biological insights",
            "research_recommendations": "Actionable next steps",
            "experimental_approaches": "Suggested methodologies",
            "limitations": "Data quality assessment"
        }
    }

# Example usage for testing
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FoldSearch API server with GPT-4o Analysis...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
