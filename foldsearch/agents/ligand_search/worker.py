import openai
import json
import time
from dotenv import load_dotenv
from agents.ligand_search.models import (
    ToolsToUseResult, 
    BaseLigandSearchResult,
    SearchLigandsToolResult,
    LigandSearchResponse,
    LigandInfo
)
from agents.ligand_search.tooling import (
    search_ligands
)
from agents.ligand_search.prompts import LIGAND_SEARCH_USAGE_TOOL_CALL
from agents.ligand_search.openai_tooling_dict import (
    search_ligands_tool
)
import asyncio
import json
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Tool registry mapping tool names to their implementations
ALL_TOOLS_DICT = {
    "search_ligands_tool": {
        "openai_tool": search_ligands_tool,
        "function": search_ligands
    }
}

load_dotenv()

# Tool selection prompt - determines which tools to use based on user query
TOOL_SELECTION_PROMPT = f"""
You are an expert cheminformatician. Based on the user query, determine which tools to use for the best results.

Available tools: {list(ALL_TOOLS_DICT.keys())}

Tool Selection Guidelines:
- search_ligands_tool: For general ligand searches, compound names, SMILES

Choose 1-3 tools that will best answer the user's query. Prefer parallel execution when possible.
Return only the tool names as a list.
"""

class LigandSearchAgent:
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
            return ["search_ligands_tool"]
    
    def get_tool_arguments(self, query: str, tool_name: str) -> Dict[str, Any]:
        """
        Get the appropriate arguments for a specific tool based on the user query
        """
        try:
            tool_config = ALL_TOOLS_DICT[tool_name]
            
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": LIGAND_SEARCH_USAGE_TOOL_CALL},
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
    
    def convert_to_structured_result(self, tool_result: Dict[str, Any]) -> BaseLigandSearchResult:
        """
        Convert raw tool result to structured result model with comprehensive data
        """
        tool_name = tool_result["tool_name"]
        success = tool_result["success"]
        execution_time = tool_result["execution_time"]
        arguments = tool_result["arguments"]
        raw_result = tool_result["result"]
        error_message = tool_result["error"] or ""
        
        # Common fields for all results - ensure no None values
        common_fields = {
            "success": success,
            "execution_time": execution_time,
            "query_params": arguments or {},
            "error_message": error_message,
            "timestamp": datetime.now(),
            "ligands": [],
            "search_metadata": {}
        }
        
        # Extract and enhance common fields from raw result
        if raw_result and isinstance(raw_result, dict):
            raw_ligands_data = raw_result.get("ligands", [])
            
            common_fields.update({
                "total_count": raw_result.get("total_count", len(raw_ligands_data)),
                "search_metadata": raw_result.get("metadata", {})
            })

            # Convert raw ligands to LigandInfo objects
            ligands = []
            for ligand_data in raw_ligands_data:
                ligand_info = LigandInfo.from_chembl(ligand_data)
                ligands.append(ligand_info)

            common_fields["ligands"] = ligands
        
        # Create tool-specific result models with enhanced data
        if tool_name == "search_ligands_tool":
            return SearchLigandsToolResult(
                **common_fields,
                search_query=arguments.get("query", ""),
                search_type=arguments.get("search_type", "name"),
                exact_match=arguments.get("exact_match", False)
            )
        
        # Fallback to base result if tool not recognized
        return BaseLigandSearchResult(**common_fields, tool_name=tool_name)
    
    def search(self, query: str) -> LigandSearchResponse:
        """
        Main search method - orchestrates the entire workflow
        1. Determine which tools to use
        2. Execute tools in parallel
        3. Convert results to structured models
        4. Return as LigandSearchResponse
        """
        print(f"🔍 Processing ligand search query: {query}")

        start_time = time.time()

        try:
            # Step 1: Determine tools to use
            selected_tools = self.determine_tools_to_use(query)
            print(f"📋 Selected tools: {selected_tools}")

            # Step 2: Execute tools in parallel
            print(f"⚡ Executing {len(selected_tools)} tools in parallel...")
            raw_tool_results = self.execute_tools_parallel(query, selected_tools)

            # Step 3: Convert to structured results
            print("📊 Converting to structured results...")
            structured_results = []
            successful_tools = 0
            failed_tools = 0

            for raw_result in raw_tool_results:
                structured_result = self.convert_to_structured_result(raw_result)
                structured_results.append(structured_result)

                if structured_result.success:
                    successful_tools += 1
                else:
                    failed_tools += 1

            total_execution_time = time.time() - start_time

            # Step 4: Create response
            response = LigandSearchResponse(
                success=successful_tools > 0,
                results=structured_results,
                total_execution_time=total_execution_time,
                tools_used=selected_tools,
                summary={
                    "query": query,
                    "total_tools_used": len(selected_tools),
                    "successful_tools": successful_tools,
                    "failed_tools": failed_tools,
                    "unique_ligands_found": len(
                        {
                            lid.chembl_id
                            for result in structured_results
                            for lid in result.ligands
                        }
                    ),
                },
            )

            # Summary
            total_unique = response.summary.get("unique_ligands_found", 0)
            print("✅ Search completed successfully!")
            print(f"   - Tools used: {len(selected_tools)}")
            print(f"   - Successful tools: {successful_tools}")
            print(f"   - Failed tools: {failed_tools}")
            print(f"   - Unique ligand IDs found: {total_unique}")
            print(f"   - Total execution time: {total_execution_time:.2f}s")

            return response

        except Exception as e:
            print(f"❌ Error in ligand search: {e}")
            total_execution_time = time.time() - start_time

            return LigandSearchResponse(
                success=False,
                results=structured_results if 'structured_results' in locals() else [],
                total_execution_time=total_execution_time,
                tools_used=[],
                error_message=str(e)
            )
    