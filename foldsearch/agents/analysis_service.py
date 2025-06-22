import openai
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

class BiologicalAnalysis(BaseModel):
    """Simple biological analysis model"""
    query: str
    analysis_type: str  # 'web', 'protein', 'combined'
    analysis_text: str = ""  # Simple paragraph analysis
    
    # Metadata
    timestamp: datetime
    analysis_model: str = "gpt-4o"
    processing_time: float = 0.0

class AnalysisService:
    """Service for generating scientific analysis using GPT-4o"""
    
    def __init__(self):
        self.client = openai.OpenAI()
        self.model = "gpt-4o"
    
    def _prepare_web_data_for_analysis(self, web_data: Dict[str, Any]) -> str:
        """Extract and format web research data for analysis"""
        if not web_data or not isinstance(web_data, dict):
            return "No web research data available."
        
        formatted_data = []
        
        # Extract research papers
        if "research_paper" in web_data and web_data["research_paper"]:
            research_paper = web_data["research_paper"]
            if "search_result" in research_paper:
                formatted_data.append("**Research Papers Found:**")
                for i, result in enumerate(research_paper["search_result"][:10], 1):  # Limit to 10 for analysis
                    formatted_data.append(f"{i}. **{result.get('title', 'Unknown Title')}**")
                    formatted_data.append(f"   - URL: {result.get('url', 'N/A')}")
                    formatted_data.append(f"   - Abstract: {result.get('abstract', 'No abstract available')[:500]}...")
                    formatted_data.append("")
        
        # Extract follow-up queries
        if "upnext_queries" in web_data and web_data["upnext_queries"]:
            formatted_data.append("**Suggested Follow-up Research Areas:**")
            for query in web_data["upnext_queries"][:5]:
                formatted_data.append(f"- {query}")
            formatted_data.append("")
        
        return "\n".join(formatted_data) if formatted_data else "No significant web research data found."
    
    def _prepare_protein_data_for_analysis(self, protein_data: Dict[str, Any]) -> str:
        """Extract and format protein search data for analysis"""
        if not protein_data:
            return "No protein structure data available."
        
        formatted_data = []
        
        # Process each tool result
        for tool_name, tool_result in protein_data.items():
            if tool_name == "web_search_tool":
                continue
                
            if not tool_result or not hasattr(tool_result, 'success'):
                continue
                
            if tool_result.success:
                formatted_data.append(f"**{tool_name.replace('_', ' ').title()}:**")
                
                # Extract PDB IDs
                if hasattr(tool_result, 'pdb_ids') and tool_result.pdb_ids:
                    formatted_data.append(f"- Found {len(tool_result.pdb_ids)} structures: {', '.join(tool_result.pdb_ids[:10])}")
                
                # Extract structure details
                if hasattr(tool_result, 'structures') and tool_result.structures:
                    for structure in tool_result.structures[:5]:  # Limit to 5 for analysis
                        formatted_data.append(f"  - {structure.pdb_id}: {structure.title}")
                        if structure.method:
                            formatted_data.append(f"    Method: {structure.method}")
                        if structure.resolution_A > 0:
                            formatted_data.append(f"    Resolution: {structure.resolution_A}Å")
                        if structure.organisms:
                            formatted_data.append(f"    Organisms: {', '.join(structure.organisms[:3])}")
                
                # Extract sequence information
                if hasattr(tool_result, 'sequences') and tool_result.sequences:
                    formatted_data.append(f"- Found {len(tool_result.sequences)} sequences")
                    for seq_id, seq_info in list(tool_result.sequences.items())[:3]:
                        formatted_data.append(f"  - {seq_id}: {seq_info.description[:100]}...")
                
                # Extract interaction data
                if hasattr(tool_result, 'interactions') and tool_result.interactions:
                    formatted_data.append(f"- Found interactions in {len(tool_result.interactions)} structures")
                
                formatted_data.append("")
        
        return "\n".join(formatted_data) if formatted_data else "No significant protein structure data found."
    
    def _create_analysis_prompt(self, query: str, web_data: str, protein_data: str, analysis_type: str) -> str:
        """Create a simple analysis prompt for GPT-4o"""
        
        prompt = f"""You are a computational biologist. Analyze the following research data for the query: "{query}"

DATA SOURCES:
{web_data}

{protein_data}

Please provide a concise biological analysis in 2-3 paragraphs that covers:
- What these results show and their biological significance
- Key structural or functional insights from the data
- Potential applications for drug design or research
- Any notable patterns or relationships in the findings

Write this as a clear, scientific summary that would be useful for a biologist researching this topic. Focus on the most important biological insights and practical implications."""

        return prompt
    
    async def generate_analysis(self, query: str, search_results: Dict[str, Any], analysis_type: str = "combined") -> BiologicalAnalysis:
        """Generate comprehensive biological analysis using GPT-4o"""
        
        start_time = datetime.now()
        
        try:
            # Prepare data for analysis
            web_data = ""
            protein_data = ""
            
            if "web_search_tool" in search_results:
                web_data = self._prepare_web_data_for_analysis(search_results["web_search_tool"])
                
            # Extract protein data (everything that's not web search)
            protein_results = {k: v for k, v in search_results.items() if k != "web_search_tool"}
            if protein_results:
                protein_data = self._prepare_protein_data_for_analysis(protein_results)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(query, web_data, protein_data, analysis_type)
            
            # Generate analysis using GPT-4o
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a world-class computational biologist and bioinformatics expert with deep expertise in protein structures, molecular biology, and scientific research. Provide comprehensive, accurate, and actionable analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for more consistent, factual responses
                max_tokens=4000
            )
            
            analysis_text = response.choices[0].message.content
            
            # Create simple analysis response
            analysis = BiologicalAnalysis(
                query=query,
                analysis_type=analysis_type,
                analysis_text=analysis_text,
                timestamp=datetime.now(),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
            return analysis
            
        except Exception as e:
            print(f"❌ Analysis generation failed: {e}")
            
            # Return basic analysis with error information
            return BiologicalAnalysis(
                query=query,
                analysis_type=analysis_type,
                analysis_text=f"Analysis generation failed due to: {str(e)}. Unable to process the research data for biological insights.",
                timestamp=datetime.now(),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
 