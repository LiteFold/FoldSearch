import openai
from dotenv import load_dotenv
from agents.protein_search.models import ProteinSearchUnifiedResults, ToolsToUseResult
from agents.protein_search.tooling import (
    search_structures,
    search_by_sequence,
    search_by_structure,
    search_by_chemical,
    get_high_quality_structures,
    get_structure_details,
    get_sequences,
    compare_structures,
    analyze_interactions,
    get_structural_summary
)
from agents.protein_search.prompts import PROTEIN_SEARCH_USAGE_TOOL_CALL
from agents.protein_search.openai_tooling_dict import (
    search_structures_tool,
    search_by_sequence_tool,
    search_by_structure_tool,
    search_by_chemical_tool,
    get_high_quality_structures_tool,
    get_structure_details_tool,
    get_sequences_tool,
    compare_structures_tool,
    analyze_interactions_tool,
    get_structural_summary_tool
)
import asyncio
import json
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Tool registry mapping tool names to their implementations
ALL_TOOLS_DICT = {
    "search_structures_tool": {
        "openai_tool": search_structures_tool, 
        "function": search_structures
    },
    "search_by_sequence_tool": {
        "openai_tool": search_by_sequence_tool,
        "function": search_by_sequence
    },
    "search_by_structure_tool": {
        "openai_tool": search_by_structure_tool,
        "function": search_by_structure
    },
    "search_by_chemical_tool": {
        "openai_tool": search_by_chemical_tool,
        "function": search_by_chemical
    },
    "get_high_quality_structures_tool": {
        "openai_tool": get_high_quality_structures_tool,
        "function": get_high_quality_structures
    },
    "get_structure_details_tool": {
        "openai_tool": get_structure_details_tool,
        "function": get_structure_details
    },
    "get_sequences_tool": {
        "openai_tool": get_sequences_tool,
        "function": get_sequences
    },
    "compare_structures_tool": {
        "openai_tool": compare_structures_tool,
        "function": compare_structures
    },
    "analyze_interactions_tool": {
        "openai_tool": analyze_interactions_tool,
        "function": analyze_interactions
    },
    "get_structural_summary_tool": {
        "openai_tool": get_structural_summary_tool,
        "function": get_structural_summary
    }
}

load_dotenv()

# Tool selection prompt - determines which tools to use based on user query
TOOL_SELECTION_PROMPT = f"""
You are an expert protein research assistant. Based on the user query, determine which tools to use for the best results.

Available tools: {list(ALL_TOOLS_DICT.keys())}

Tool Selection Guidelines:
- search_structures_tool: For general protein searches, keywords, organism names
- search_by_sequence_tool: When user provides a protein/DNA/RNA sequence 
- search_by_structure_tool: When user provides PDB IDs and wants similar structures
- search_by_chemical_tool: When user mentions ligands, drugs, chemical compounds
- get_high_quality_structures_tool: When user specifically wants high-resolution/quality structures
- get_structure_details_tool: When user asks for detailed information about specific PDB IDs
- get_sequences_tool: When user wants sequences from specific PDB IDs
- compare_structures_tool: When user wants to compare multiple structures
- analyze_interactions_tool: When user asks about protein-protein or protein-ligand interactions
- get_structural_summary_tool: When user wants comprehensive summaries/overviews

Choose 1-3 tools that will best answer the user's query. Prefer parallel execution when possible.
Return only the tool names as a list.
"""


class ProteinSearchAgent:
    def __init__(self):
        self.client = openai.OpenAI()
        
    def determine_tools_to_use(self, query: str) -> List[str]:
        """
        Determine which tools to use based on the user query
        Uses LLM to intelligently select the most appropriate tools
        """
        try:
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": TOOL_SELECTION_PROMPT},
                    {"role": "user", "content": f"User query: {query}"}
                ],
                response_format=ToolsToUseResult
            )
            return completion.choices[0].message.parsed.tools_to_use
        except Exception as e:
            print(f"Error in tool selection: {e}")
            # Fallback to general search if tool selection fails
            return ["search_structures_tool"]
    
    def get_tool_arguments(self, query: str, tool_name: str) -> Dict[str, Any]:
        """
        Get the appropriate arguments for a specific tool based on the user query
        """
        try:
            tool_config = ALL_TOOLS_DICT[tool_name]
            
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": PROTEIN_SEARCH_USAGE_TOOL_CALL},
                    {"role": "user", "content": f"Based on this query: '{query}', determine the arguments for the tool."}
                ],
                tools=[tool_config["openai_tool"]],
                tool_choice={"type": "function", "function": {"name": tool_config["openai_tool"]["function"]["name"]}}
            )
            
            tool_call = completion.choices[0].message.tool_calls[0]
            return json.loads(tool_call.function.arguments)
        except Exception as e:
            print(f"Error getting tool arguments for {tool_name}: {e}")
            return {}
    
    def execute_tool_parallel(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single tool with given arguments
        Returns the result with metadata
        """
        start_time = time.time()
        
        try:
            tool_config = ALL_TOOLS_DICT[tool_name]
            result = tool_config["function"](**arguments)
            
            execution_time = time.time() - start_time
            
            return {
                "tool_name": tool_name,
                "success": True,
                "result": result,
                "arguments": arguments,
                "execution_time": execution_time,
                "error": None
            }
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"Error executing {tool_name}: {e}")
            
            return {
                "tool_name": tool_name,
                "success": False,
                "result": None,
                "arguments": arguments,
                "execution_time": execution_time,
                "error": str(e)
            }
    
    def execute_tools_parallel(self, query: str, selected_tools: List[str]) -> List[Dict[str, Any]]:
        """
        Execute multiple tools in parallel for maximum efficiency
        """
        # Get arguments for each tool
        tool_executions = []
        for tool_name in selected_tools:
            arguments = self.get_tool_arguments(query, tool_name)
            tool_executions.append((tool_name, arguments))
        
        # Execute all tools in parallel using ThreadPoolExecutor
        results = []
        with ThreadPoolExecutor(max_workers=min(len(tool_executions), 5)) as executor:
            # Submit all tasks
            future_to_tool = {
                executor.submit(self.execute_tool_parallel, tool_name, args): tool_name 
                for tool_name, args in tool_executions
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_tool):
                result = future.result()
                results.append(result)
        
        return results
    
    def aggregate_results(self, query: str, tool_results: List[Dict[str, Any]]) -> ProteinSearchUnifiedResults:
        """
        Aggregate results from multiple tools into a unified DTO
        Uses intelligent merging and deduplication
        """
        start_time = time.time()
        
        # Initialize the unified result
        unified_result = ProteinSearchUnifiedResults(
            query_params={"original_query": query},
            timestamp=datetime.now(),
            execution_time=0.0,
            success=True,
            operation_type="multi_tool_search"
        )
        
        # Track aggregated data
        all_pdb_ids = set()
        all_scores = {}
        all_errors = []
        successful_tools = []
        total_structures = 0
        
        # Process each tool result
        for tool_result in tool_results:
            tool_name = tool_result["tool_name"]
            
            if not tool_result["success"]:
                all_errors.append(f"{tool_name}: {tool_result['error']}")
                continue
                
            successful_tools.append(tool_name)
            result_data = tool_result["result"]
            
            if result_data and isinstance(result_data, dict):
                # Extract PDB IDs
                if "pdb_ids" in result_data:
                    pdb_ids = result_data["pdb_ids"]
                    if isinstance(pdb_ids, list):
                        all_pdb_ids.update(pdb_ids)
                        total_structures += len(pdb_ids)
                
                # Extract scores
                if "scores" in result_data:
                    scores = result_data["scores"]
                    if isinstance(scores, dict):
                        all_scores.update(scores)
                
                # Store tool-specific data
                if tool_name == "search_structures_tool":
                    unified_result.search_query = query
                elif tool_name == "get_structure_details_tool":
                    unified_result.structure_details = result_data
                elif tool_name == "get_sequences_tool":
                    unified_result.sequences = result_data
                elif tool_name == "compare_structures_tool":
                    unified_result.comparisons = result_data
                elif tool_name == "analyze_interactions_tool":
                    unified_result.interactions = result_data
        
        # Set aggregated fields
        unified_result.pdb_ids = list(all_pdb_ids) if all_pdb_ids else None
        unified_result.scores = all_scores if all_scores else None
        unified_result.total_count = len(all_pdb_ids) if all_pdb_ids else 0
        unified_result.returned_count = len(all_pdb_ids) if all_pdb_ids else 0
        unified_result.total_structures = total_structures
        unified_result.successful_retrievals = len(successful_tools)
        unified_result.failed_retrievals = len(all_errors)
        unified_result.warnings = all_errors if all_errors else None
        unified_result.execution_time = time.time() - start_time
        unified_result.success = len(successful_tools) > 0
        unified_result.tool_used = ", ".join(successful_tools)
        
        # Add raw results for debugging
        unified_result.raw_response = {
            "tool_results": tool_results,
            "selected_tools": successful_tools
        }
        
        return unified_result
    
    def search(self, query: str) -> ProteinSearchUnifiedResults:
        """
        Main search method - orchestrates the entire workflow
        1. Determine which tools to use
        2. Execute tools in parallel
        3. Aggregate results into unified DTO
        """
        print(f"🔍 Processing protein search query: {query}")
        
        try:
            # Step 1: Determine tools to use
            selected_tools = self.determine_tools_to_use(query)
            print(f"📋 Selected tools: {selected_tools}")
            
            # Step 2: Execute tools in parallel
            print(f"⚡ Executing {len(selected_tools)} tools in parallel...")
            tool_results = self.execute_tools_parallel(query, selected_tools)
            
            # Step 3: Aggregate results
            print("📊 Aggregating results...")
            unified_result = self.aggregate_results(query, tool_results)
            
            # Summary
            print(f"✅ Search completed successfully!")
            print(f"   - Tools used: {len(selected_tools)}")
            print(f"   - PDB IDs found: {unified_result.total_count}")
            print(f"   - Execution time: {unified_result.execution_time:.2f}s")
            
            return unified_result
            
        except Exception as e:
            print(f"❌ Error in protein search: {e}")
            return ProteinSearchUnifiedResults(
                success=False,
                error_message=str(e),
                query_params={"original_query": query},
                timestamp=datetime.now()
            )


# Example usage and testing
