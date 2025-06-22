import openai
from dotenv import load_dotenv
from agents.protein_search.models import (
    ToolsToUseResult, 
    BaseProteinSearchResult,
    SearchStructuresResult,
    SearchBySequenceResult,
    SearchByStructureResult,
    SearchByChemicalResult,
    GetHighQualityStructuresResult,
    GetStructureDetailsResult,
    GetSequencesResult,
    CompareStructuresResult,
    AnalyzeInteractionsResult,
    GetStructuralSummaryResult,
    ProteinSearchResponse,
    StructureInfo,
    SequenceInfo,
    ComparisonInfo,
    InteractionInfo,
    StructuralSummaryInfo,
    ProteinStructureInfo
)
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
    
    def convert_to_structured_result(self, tool_result: Dict[str, Any]) -> BaseProteinSearchResult:
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
            "pdb_ids": [],
            "total_count": 0,
            "returned_count": 0,
            "scores": {},
            "structures": [],
            "search_metadata": {}
        }
        
        # Extract and enhance common fields from raw result
        if raw_result and isinstance(raw_result, dict):
            pdb_ids = raw_result.get("pdb_ids", [])
            scores = raw_result.get("scores", {})
            enhanced_structures_data = raw_result.get("structures", [])
            
            common_fields.update({
                "pdb_ids": pdb_ids,
                "total_count": raw_result.get("total_count", 0),
                "returned_count": raw_result.get("returned_count", len(pdb_ids)),
                "scores": scores,
                "search_metadata": raw_result.get("metadata", {})
            })
            
            # Convert enhanced structures to ProteinStructureInfo objects
            structures = []
            for struct_data in enhanced_structures_data:
                structure_info = ProteinStructureInfo(
                    pdb_id=struct_data.get("pdb_id", ""),
                    title=struct_data.get("title", ""),
                    method=struct_data.get("method", ""),
                    resolution_A=struct_data.get("resolution_A", 0.0),
                    r_work=struct_data.get("r_work", 0.0),
                    r_free=struct_data.get("r_free", 0.0),
                    space_group=struct_data.get("space_group", ""),
                    deposition_date=struct_data.get("deposition_date", ""),
                    organisms=struct_data.get("organisms", []),
                    protein_chains=struct_data.get("protein_chains", []),
                    ligands=struct_data.get("ligands", []),
                    entities=struct_data.get("entities", []),
                    assembly=struct_data.get("assembly", {}),
                    quality_score=struct_data.get("quality_score", ""),
                    sequence=struct_data.get("sequence", ""),
                    sequence_length=struct_data.get("sequence_length", 0),
                    molecule_type=struct_data.get("molecule_type", ""),
                    score=struct_data.get("score", 0.0)
                )
                structures.append(structure_info)
            
            common_fields["structures"] = structures
        
        # Create tool-specific result models with enhanced data
        if tool_name == "search_structures_tool":
            # Extract additional metadata from structures
            organisms_found = list(set([org for s in common_fields["structures"] for org in s.organisms if org]))
            methods_found = list(set([s.method for s in common_fields["structures"] if s.method and s.method != "Unknown"]))
            resolutions = [s.resolution_A for s in common_fields["structures"] if s.resolution_A > 0]
            
            return SearchStructuresResult(
                **common_fields,
                search_query=arguments.get("query", ""),
                organism=arguments.get("organism", ""),
                method=arguments.get("method", ""),
                max_resolution=arguments.get("max_resolution", 0.0),
                organisms_found=organisms_found,
                methods_found=methods_found,
                resolution_range={
                    "min": min(resolutions) if resolutions else 0.0,
                    "max": max(resolutions) if resolutions else 0.0
                }
            )
        elif tool_name == "search_by_sequence_tool":
            sequence = arguments.get("sequence", "")
            return SearchBySequenceResult(
                **common_fields,
                sequence=sequence,
                sequence_type=arguments.get("sequence_type", "protein"),
                identity_cutoff=arguments.get("identity_cutoff", 0.5),
                evalue_cutoff=arguments.get("evalue_cutoff", 1.0),
                sequence_length=len(sequence),
                alignment_data=[],  # Would be populated with actual alignment data
                identity_scores=common_fields["scores"],
                evalue_scores={}  # Would be populated with E-values
            )
        elif tool_name == "search_by_structure_tool":
            return SearchByStructureResult(
                **common_fields,
                reference_pdb_ids=arguments.get("reference_pdb_ids", []),
                assembly_id=arguments.get("assembly_id", "1"),
                match_type=arguments.get("match_type", "relaxed"),
                similarity_scores=common_fields["scores"],
                structural_matches={},
                by_reference=raw_result.get("by_reference", {}) if raw_result else {}
            )
        elif tool_name == "search_by_chemical_tool":
            # Extract ligand information from structures
            ligands_found = []
            binding_sites = {}
            for struct in common_fields["structures"]:
                if struct.ligands:
                    for ligand in struct.ligands:
                        ligand_info = {
                            "pdb_id": struct.pdb_id,
                            "ligand_name": ligand,
                            "binding_context": f"Found in {struct.title}"
                        }
                        ligands_found.append(ligand_info)
                        
                        if struct.pdb_id not in binding_sites:
                            binding_sites[struct.pdb_id] = []
                        binding_sites[struct.pdb_id].append({
                            "ligand": ligand,
                            "chains": struct.protein_chains
                        })
            
            return SearchByChemicalResult(
                **common_fields,
                chemical_identifier=arguments.get("identifier", ""),
                identifier_type=arguments.get("identifier_type", "SMILES"),
                ligand_name=arguments.get("ligand_name", ""),
                match_type=arguments.get("match_type", "graph-relaxed"),
                ligands_found=ligands_found,
                binding_sites=binding_sites,
                chemical_properties={}
            )
        elif tool_name == "get_high_quality_structures_tool":
            # Calculate quality statistics
            quality_distribution = {}
            resolution_stats = {}
            yearly_distribution = {}
            
            resolutions = [s.resolution_A for s in common_fields["structures"] if s.resolution_A > 0]
            if resolutions:
                resolution_stats = {
                    "mean": sum(resolutions) / len(resolutions),
                    "min": min(resolutions),
                    "max": max(resolutions),
                    "count": len(resolutions)
                }
            
            # Extract years from deposition dates
            for struct in common_fields["structures"]:
                if struct.deposition_date:
                    try:
                        year = int(struct.deposition_date[:4])
                        yearly_distribution[year] = yearly_distribution.get(year, 0) + 1
                    except (ValueError, IndexError):
                        pass
            
            return GetHighQualityStructuresResult(
                **common_fields,
                max_resolution=arguments.get("max_resolution", 2.0),
                max_r_work=arguments.get("max_r_work", 0.25),
                max_r_free=arguments.get("max_r_free", 0.28),
                method=arguments.get("method", "X-RAY DIFFRACTION"),
                min_year=arguments.get("min_year", 2000),
                quality_distribution=quality_distribution,
                resolution_stats=resolution_stats,
                yearly_distribution=yearly_distribution
            )
        elif tool_name == "get_structure_details_tool":
            structure_details = {}
            structure_types = []
            experimental_methods = []
            organism_diversity = {}
            
            # Use the enhanced structures data
            for struct in common_fields["structures"]:
                structure_info = StructureInfo(
                    pdb_id=struct.pdb_id,
                    title=struct.title,
                    method=struct.method,
                    resolution_A=struct.resolution_A,
                    r_work=struct.r_work,
                    r_free=struct.r_free,
                    space_group=struct.space_group,
                    deposition_date=struct.deposition_date,
                    organisms=struct.organisms,
                    ligands=struct.ligands,
                    entities=struct.entities,
                    assembly=struct.assembly,
                    quality_score=struct.quality_score
                )
                structure_details[struct.pdb_id] = structure_info
                
                # Collect metadata
                if struct.method and struct.method not in experimental_methods:
                    experimental_methods.append(struct.method)
                for org in struct.organisms:
                    if org:
                        organism_diversity[org] = organism_diversity.get(org, 0) + 1
            
            return GetStructureDetailsResult(
                **common_fields,
                structure_details=structure_details,
                include_assembly=arguments.get("include_assembly", True),
                structure_types=list(set(structure_types)),
                experimental_methods=experimental_methods,
                organism_diversity=organism_diversity
            )
        elif tool_name == "get_sequences_tool":
            sequences = {}
            sequence_stats = {}
            length_distribution = {}
            type_distribution = {}
            
            # Use enhanced structure data for sequences
            for struct in common_fields["structures"]:
                if struct.sequence:
                    sequence_key = f"{struct.pdb_id}_1"
                    sequence_info = SequenceInfo(
                        pdb_id=struct.pdb_id,
                        entity_id="1",
                        sequence=struct.sequence,
                        sequence_length=struct.sequence_length,
                        sequence_type=struct.molecule_type,
                        molecule_type=struct.molecule_type,
                        organism=struct.organisms[0] if struct.organisms else "",
                        description=struct.title
                    )
                    sequences[sequence_key] = sequence_info
                    
                    # Collect statistics
                    seq_len = struct.sequence_length
                    length_range = f"{seq_len//100*100}-{seq_len//100*100+99}"
                    length_distribution[length_range] = length_distribution.get(length_range, 0) + 1
                    
                    if struct.molecule_type:
                        type_distribution[struct.molecule_type] = type_distribution.get(struct.molecule_type, 0) + 1
            
            # Also include raw sequence data if present
            if raw_result:
                for key, seq_data in raw_result.items():
                    if isinstance(seq_data, dict) and "error" not in seq_data and key not in sequences:
                        sequence_info = SequenceInfo(
                            pdb_id=seq_data.get("pdb_id", ""),
                            entity_id=seq_data.get("entity_id", ""),
                            sequence=seq_data.get("sequence", ""),
                            sequence_length=seq_data.get("length", 0),
                            sequence_type=seq_data.get("type", ""),
                            molecule_type=seq_data.get("type", ""),
                            organism="",
                            description=""
                        )
                        sequences[key] = sequence_info
            
            return GetSequencesResult(
                **common_fields,
                sequences=sequences,
                entity_ids=arguments.get("entity_ids", []),
                sequence_stats=sequence_stats,
                length_distribution=length_distribution,
                type_distribution=type_distribution
            )
        elif tool_name == "compare_structures_tool":
            comparisons = {}
            similarity_matrix = {}
            
            if raw_result and "comparisons" in raw_result:
                for pair_key, comp_data in raw_result["comparisons"].items():
                    comparison_info = ComparisonInfo(
                        pdb_pair=pair_key,
                        sequence_identity=comp_data.get("sequence_identity", 0.0),
                        length_difference=comp_data.get("length_difference", 0),
                        structural_similarity=comp_data.get("structural_similarity", 0.0),
                        comparison_note=comp_data.get("note", ""),
                        rmsd=comp_data.get("rmsd", 0.0),
                        alignment_length=comp_data.get("alignment_length", 0)
                    )
                    comparisons[pair_key] = comparison_info
            
            return CompareStructuresResult(
                **common_fields,
                comparison_type=arguments.get("comparison_type", "both"),
                comparisons=comparisons,
                summary=raw_result.get("summary", {}) if raw_result else {},
                similarity_matrix=similarity_matrix,
                cluster_analysis={}
            )
        elif tool_name == "analyze_interactions_tool":
            interactions = {}
            interaction_summary = {}
            complex_types = {}
            binding_partners = {}
            
            if raw_result:
                for pdb_id, interaction_data in raw_result.items():
                    if isinstance(interaction_data, dict):
                        interaction_info = InteractionInfo(
                            pdb_id=pdb_id,
                            protein_chains=interaction_data.get("protein_chains", []),
                            ligands=interaction_data.get("ligands", []),
                            interactions=interaction_data.get("interactions", []),
                            quaternary_structure=interaction_data.get("quaternary_structure", {}),
                            binding_sites=[],
                            interface_area=0.0
                        )
                        interactions[pdb_id] = interaction_info
                        
                        # Collect metadata
                        if len(interaction_info.protein_chains) > 1:
                            complex_types["protein-protein"] = complex_types.get("protein-protein", 0) + 1
                        if interaction_info.ligands:
                            complex_types["protein-ligand"] = complex_types.get("protein-ligand", 0) + 1
            
            return AnalyzeInteractionsResult(
                **common_fields,
                interaction_type=arguments.get("interaction_type", "all"),
                interactions=interactions,
                interaction_summary=interaction_summary,
                complex_types=complex_types,
                binding_partners=binding_partners
            )
        elif tool_name == "get_structural_summary_tool":
            summaries = {}
            research_trends = {}
            quality_overview = {}
            functional_categories = {}
            
            # Use enhanced structure data for summaries
            for struct in common_fields["structures"]:
                summary_info = StructuralSummaryInfo(
                    pdb_id=struct.pdb_id,
                    title=struct.title,
                    experimental={
                        "method": struct.method,
                        "resolution_A": struct.resolution_A,
                        "r_work": struct.r_work,
                        "r_free": struct.r_free,
                        "space_group": struct.space_group,
                        "deposition_date": struct.deposition_date
                    },
                    composition={
                        "organisms": struct.organisms,
                        "protein_chains": len(struct.protein_chains),
                        "ligands": len(struct.ligands),
                        "entities": len(struct.entities)
                    },
                    biological_assembly=struct.assembly,
                    research_relevance={
                        "has_ligands": len(struct.ligands) > 0,
                        "multi_chain": len(struct.protein_chains) > 1,
                        "sequence_available": len(struct.sequence) > 0
                    },
                    quality={
                        "resolution_A": struct.resolution_A,
                        "r_work": struct.r_work,
                        "r_free": struct.r_free,
                        "quality_score": struct.quality_score
                    },
                    organisms=struct.organisms,
                    functional_classification=struct.molecule_type,
                    research_applications=["Structural Biology", "Drug Discovery"] if struct.ligands else ["Structural Biology"]
                )
                summaries[struct.pdb_id] = summary_info
            
            # Also include raw summary data if present
            if raw_result:
                for pdb_id, summary_data in raw_result.items():
                    if isinstance(summary_data, dict) and "error" not in summary_data and pdb_id not in summaries:
                        summary_info = StructuralSummaryInfo(
                            pdb_id=pdb_id,
                            title=summary_data.get("title", ""),
                            experimental=summary_data.get("experimental", {}),
                            composition=summary_data.get("composition", {}),
                            biological_assembly=summary_data.get("biological_assembly", {}),
                            research_relevance=summary_data.get("research_relevance", {}),
                            quality=summary_data.get("quality", {}),
                            organisms=summary_data.get("organisms", []),
                            functional_classification="",
                            research_applications=[]
                        )
                        summaries[pdb_id] = summary_info
            
            return GetStructuralSummaryResult(
                **common_fields,
                include_quality_metrics=arguments.get("include_quality_metrics", True),
                summaries=summaries,
                research_trends=research_trends,
                quality_overview=quality_overview,
                functional_categories=functional_categories
            )
        
        # Fallback to base result if tool not recognized
        return BaseProteinSearchResult(**common_fields, tool_name=tool_name)
    
    def search(self, query: str) -> ProteinSearchResponse:
        """
        Main search method - orchestrates the entire workflow
        1. Determine which tools to use
        2. Execute tools in parallel
        3. Convert results to structured models
        4. Return as ProteinSearchResponse
        """
        print(f"🔍 Processing protein search query: {query}")
        
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
            response = ProteinSearchResponse(
                query=query,
                tool_results=structured_results,
                total_tools_used=len(selected_tools),
                successful_tools=successful_tools,
                failed_tools=failed_tools,
                total_execution_time=total_execution_time,
                success=successful_tools > 0
            )
            
            # Summary
            total_unique = response.get_total_structures_found()
            print(f"✅ Search completed successfully!")
            print(f"   - Tools used: {len(selected_tools)}")
            print(f"   - Successful tools: {successful_tools}")
            print(f"   - Failed tools: {failed_tools}")
            print(f"   - Unique PDB IDs found: {total_unique}")
            print(f"   - Total execution time: {total_execution_time:.2f}s")
            
            return response
            
        except Exception as e:
            print(f"❌ Error in protein search: {e}")
            total_execution_time = time.time() - start_time
            
            return ProteinSearchResponse(
                query=query,
                tool_results=[],
                total_tools_used=0,
                successful_tools=0,
                failed_tools=1,
                total_execution_time=total_execution_time,
                success=False
            )


# Example usage and testing
