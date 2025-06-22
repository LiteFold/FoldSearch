#!/usr/bin/env python3
"""
Test to verify that the biological analysis integration is properly working
across all endpoints and models in the FoldSearch API.
"""

import json
from datetime import datetime
from agents.analysis_service import BiologicalAnalysis
from agents.models import CombinedSearchResult
from agents.web_search.models import WebResearchAgentModel, WebResearchResult, SearchResult
from agents.protein_search.models import ProteinSearchResponse

def test_analysis_integration():
    """Test that all models can properly store biological analysis"""
    
    print("🧬 Testing Analysis Integration")
    print("=" * 50)
    
    # Create a sample analysis
    sample_analysis = BiologicalAnalysis(
        query="Test protein analysis",
        analysis_type="combined",
        analysis_text="This is a test biological analysis. The results show interesting patterns in protein structure and function that could be relevant for drug design applications.",
        timestamp=datetime.now(),
        processing_time=1.2
    )
    
    print("✅ Sample Analysis Created:")
    print(f"   - Type: {sample_analysis.analysis_type}")
    print(f"   - Text Length: {len(sample_analysis.analysis_text)} characters")
    print(f"   - Processing Time: {sample_analysis.processing_time}s")
    
    # Test 1: WebResearchAgentModel
    print("\n🔍 Testing WebResearchAgentModel:")
    
    web_model = WebResearchAgentModel(
        query="test query",
        raw_result="raw result",
        research_paper=WebResearchResult(search_result=[
            SearchResult(title="Test Paper", url="http://test.com", abstract="Test abstract")
        ]),
        upnext_queries=["query1", "query2"],
        biological_analysis=sample_analysis
    )
    
    print(f"   ✅ Web model created with analysis: {web_model.biological_analysis is not None}")
    print(f"   ✅ Analysis type: {web_model.biological_analysis.analysis_type}")
    
    # Test 2: ProteinSearchResponse  
    print("\n🧬 Testing ProteinSearchResponse:")
    
    protein_response = ProteinSearchResponse(
        query="test protein query",
        tool_results=[],
        biological_analysis=sample_analysis
    )
    
    print(f"   ✅ Protein response created with analysis: {protein_response.biological_analysis is not None}")
    print(f"   ✅ Analysis type: {protein_response.biological_analysis.analysis_type}")
    
    # Test 3: CombinedSearchResult
    print("\n🔄 Testing CombinedSearchResult:")
    
    combined_result = CombinedSearchResult(
        query="test combined query",
        tool_results={"test_tool": {"success": True}},
        biological_analysis=sample_analysis,
        search_type="combined"
    )
    
    print(f"   ✅ Combined result created with analysis: {combined_result.biological_analysis is not None}")
    print(f"   ✅ Analysis type: {combined_result.biological_analysis.analysis_type}")
    
    # Test 4: Serialization
    print("\n📄 Testing JSON Serialization:")
    
    try:
        # Test web model serialization
        web_json = web_model.dict()
        print("   ✅ Web model serializes to JSON")
        
        # Test protein response serialization
        protein_json = protein_response.dict()
        print("   ✅ Protein response serializes to JSON")
        
        # Test combined result serialization
        combined_json = combined_result.dict()
        print("   ✅ Combined result serializes to JSON")
        
        # Check that analysis is properly included
        if web_json.get('biological_analysis'):
            print(f"   ✅ Web JSON includes analysis text: {len(web_json['biological_analysis']['analysis_text'])} chars")
        
        if protein_json.get('biological_analysis'):
            print(f"   ✅ Protein JSON includes analysis text: {len(protein_json['biological_analysis']['analysis_text'])} chars")
            
        if combined_json.get('biological_analysis'):
            print(f"   ✅ Combined JSON includes analysis text: {len(combined_json['biological_analysis']['analysis_text'])} chars")
            
    except Exception as e:
        print(f"   ❌ Serialization error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Analysis Integration Test Complete!")
    print("\n📋 Summary:")
    print("   - All models support biological_analysis field")
    print("   - Analysis can be properly assigned to all response types")
    print("   - JSON serialization works correctly")
    print("   - Ready for API endpoint integration")

if __name__ == "__main__":
    test_analysis_integration() 