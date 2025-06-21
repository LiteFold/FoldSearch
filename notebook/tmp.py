import openai
from dotenv import load_dotenv
from rcsb_search_tools import (
    text_search,
    sequence_search,
    structure_search,
    chemical_search,
    organism_search,
    method_search,
    high_quality_structures,
    RCSB_SEARCH_API_TOOLS,
    RCSB_SEARCH_API_TOOL_DESCRIPTIONS,
    SearchAPIUnifiedResults
)
import json
from typing import List, Dict, Any
import os

load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SearchPlanner:
    """Agent that plans which search tools to use based on the query"""
    
    def __init__(self):
        self.tools = [{
            "type": "function",
            "function": {
                "name": "plan_search",
                "description": "Plan which RCSB PDB search tools to use based on the query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tools": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tool_name": {
                                        "type": "string",
                                        "enum": list(RCSB_SEARCH_API_TOOL_DESCRIPTIONS.keys())
                                    },
                                    "reason": {
                                        "type": "string",
                                        "description": "Reason for using this tool"
                                    },
                                    "parameters": {
                                        "type": "object",
                                        "description": "Parameters to pass to the tool"
                                    }
                                },
                                "required": ["tool_name", "reason", "parameters"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["tools"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }]

    def plan(self, query: str) -> List[Dict[str, Any]]:
        """Plan which tools to use based on the query"""
        
        # Create system message explaining available tools
        tools_description = "\n".join([
            f"- {name}: {desc}" 
            for name, desc in RCSB_SEARCH_API_TOOL_DESCRIPTIONS.items()
        ])
        
        system_message = f"""You are a search planner for the RCSB PDB database.
Your job is to analyze user queries and determine which search tools would be most appropriate to use.

Available tools:
{tools_description}

For each tool you select:
1. Explain why it's appropriate for the query
2. Specify the parameters to pass to it
3. Only select tools that are truly relevant

Return a list of tools to use in order of priority."""

        # Get completion from OpenAI
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": query}
            ],
            tools=self.tools,
            tool_choice={"type": "function", "function": {"name": "plan_search"}}
        )

        # Extract and return the planned tools
        tool_call = completion.choices[0].message.tool_calls[0]
        return json.loads(tool_call.function.arguments)["tools"]

class SearchExecutor:
    """Agent that executes the planned searches"""
    
    def __init__(self):
        # Map tool names to functions
        self.tool_map = {
            "text_search": text_search,
            "sequence_search": sequence_search,
            "structure_search": structure_search,
            "chemical_search": chemical_search,
            "organism_search": organism_search,
            "method_search": method_search,
            "high_quality_structures": high_quality_structures
        }

    def execute(self, planned_tools: List[Dict[str, Any]]) -> List[SearchAPIUnifiedResults]:
        """Execute the planned searches"""
        results = []
        
        for tool_plan in planned_tools:
            tool_name = tool_plan["tool_name"]
            parameters = tool_plan["parameters"]
            
            # Get the function for this tool
            tool_func = self.tool_map[tool_name]
            
            # Execute the search
            search_result = tool_func(**parameters)
            
            # Convert to unified format
            unified_result = SearchAPIUnifiedResults(
                tool_used=tool_name,
                pdb_ids=search_result["pdb_ids"],
                total_count=search_result["total_count"],
                scores=search_result["scores"],
                returned_count=search_result["returned_count"],
                query_params=parameters
            )
            
            results.append(unified_result)
            
        return results

class ResultsAggregator:
    """Agent that aggregates and summarizes search results"""
    
    def __init__(self):
        self.tools = [{
            "type": "function",
            "function": {
                "name": "summarize_results",
                "description": "Summarize the search results in a clear way",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Summary of the search results"
                        },
                        "top_hits": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "pdb_id": {"type": "string"},
                                    "score": {"type": "number"},
                                    "tool": {"type": "string"}
                                },
                                "required": ["pdb_id", "score", "tool"]
                            }
                        }
                    },
                    "required": ["summary", "top_hits"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }]

    def aggregate(self, query: str, results: List[SearchAPIUnifiedResults]) -> Dict[str, Any]:
        """Aggregate and summarize the search results"""
        
        # Format results for the model
        results_str = "\n\n".join([
            f"Tool: {r.tool_used}\n"
            f"Found {r.total_count} results, returned {r.returned_count}\n"
            f"Top PDB IDs: {', '.join(r.pdb_ids[:5])}\n"
            f"Parameters used: {json.dumps(r.query_params, indent=2)}"
            for r in results
        ])
        
        system_message = """You are a results aggregator for RCSB PDB searches.
Your job is to analyze search results from multiple tools and provide a clear summary.
Focus on:
1. The most relevant results across all tools
2. Any patterns or interesting findings
3. Which tools were most successful"""

        # Get completion from OpenAI
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Query: {query}\n\nResults:\n{results_str}"}
            ],
            tools=self.tools,
            tool_choice={"type": "function", "function": {"name": "summarize_results"}}
        )

        # Extract and return the summary
        tool_call = completion.choices[0].message.tool_calls[0]
        return json.loads(tool_call.function.arguments)

class SearchAgent:
    """Main agent that coordinates the search process"""
    
    def __init__(self):
        self.planner = SearchPlanner()
        self.executor = SearchExecutor()
        self.aggregator = ResultsAggregator()
    
    def search(self, query: str) -> Dict[str, Any]:
        """Execute a complete search process"""
        
        # 1. Plan the search
        planned_tools = self.planner.plan(query)
        
        # 2. Execute the searches
        search_results = self.executor.execute(planned_tools)
        
        # 3. Aggregate and summarize results
        final_results = self.aggregator.aggregate(query, search_results)
        
        return final_results

# Example usage
if __name__ == "__main__":
    agent = SearchAgent()
    query = "Find high-quality structures of human hemoglobin with good resolution"
    results = agent.search(query)
    print(json.dumps(results, indent=2))






# ----------------------------------------------------------------------


text_search_tool = {
    "type": "function",
    "function": {
        "name": "text_search",
        "description": """"
        You can search with basic text based query which could be either
        a protein name or a PDB-ID or a protein residue. If you search using simple text query then it would return the following json
        key: pdb_ids: contains a list of PDB ids
        key: scores: the match score of the PDB w.r.t the query
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The text query to search. Example: haptoglobin or 3BCQ",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to get from",
                },
            },
            "required": ["query", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

sequence_search_tool = {
    "type": "function",
    "function": {
        "name": "sequence_search",
        "description": """"
        You can search for similar sequences using BLAST-like algorithm with an amino acid or nucleotide sequence.
        The search will return structures containing sequences similar to your query sequence.
        It returns the following json:
        key: pdb_ids: contains a list of PDB ids
        key: scores: the match score of the PDB w.r.t the query sequence
        key: total_count: total number of matches found
        key: returned_count: number of results returned (limited by limit parameter)
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "sequence": {
                    "type": "string",
                    "description": "The sequence to search for (amino acid or nucleotide sequence in one-letter code). Example: VHLSAEEKEAVLGLWGKVNVDEVGGEALGRLLVVYPWTQRF",
                },
                "sequence_type": {
                    "type": "string",
                    "description": "Type of sequence to search",
                    "enum": ["protein", "dna", "rna"],
                },
                "identity_cutoff": {
                    "type": "number",
                    "description": "Minimum sequence identity threshold (0.0-1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "evalue_cutoff": {
                    "type": "number",
                    "description": "Maximum E-value threshold for matches",
                    "minimum": 0.0,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                },
            },
            "required": ["sequence", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

structure_search_tool = {
    "type": "function",
    "function": {
        "name": "structure_search",
        "description": """"
        You can search for structures with similar 3D shape using a reference PDB structure.
        The search will return structures that have similar overall shape to the query structure.
        It returns the following json:
        key: pdb_ids: contains a list of PDB ids
        key: scores: the match score of the PDB w.r.t the query structure (1.0 is exact match)
        key: total_count: total number of matches found
        key: returned_count: number of results returned (limited by limit parameter)
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "pdb_id": {
                    "type": "string",
                    "description": "Reference PDB ID for shape comparison. Example: 2PGH",
                },
                "assembly_id": {
                    "type": "string",
                    "description": "Assembly ID of reference structure",
                    "default": "1",
                },
                "match_type": {
                    "type": "string",
                    "description": "Type of shape matching to perform",
                    "enum": ["strict", "relaxed"],
                    "default": "relaxed",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                },
            },
            "required": ["pdb_id", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

chemical_search_tool = {
    "type": "function",
    "function": {
        "name": "chemical_search",
        "description": """"
        You can search for structures containing similar chemical compounds using SMILES or InChI identifiers.
        The search will return structures that contain chemical components matching your query.
        It returns the following json:
        key: pdb_ids: contains a list of PDB ids
        key: scores: the match score of the PDB w.r.t the query chemical (1.0 is exact match)
        key: total_count: total number of matches found
        key: returned_count: number of results returned (limited by limit parameter)
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Chemical identifier string. Example SMILES: CC(=O)O for acetic acid",
                },
                "identifier_type": {
                    "type": "string",
                    "description": "Type of chemical identifier being used",
                    "enum": ["SMILES", "InChI"],
                    "default": "SMILES",
                },
                "match_type": {
                    "type": "string",
                    "description": "Type of chemical matching to perform",
                    "enum": ["graph-strict", "graph-relaxed", "fingerprint-similarity"],
                    "default": "graph-relaxed",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                },
            },
            "required": ["identifier", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

organism_search_tool = {
    "type": "function",
    "function": {
        "name": "organism_search",
        "description": """"
        You can search for structures from a specific source organism using its scientific name.
        The search will return structures that were determined from the specified organism.
        It returns the following json:
        key: pdb_ids: contains a list of PDB ids
        key: scores: the match score of the PDB w.r.t the query organism (1.0 indicates exact match)
        key: total_count: total number of matches found
        key: returned_count: number of results returned (limited by limit parameter)
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "organism": {
                    "type": "string",
                    "description": "Scientific name of the organism. Example: 'Homo sapiens' for human proteins",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                },
            },
            "required": ["organism", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

method_search_tool = {
    "type": "function",
    "function": {
        "name": "method_search",
        "description": """"
        You can search for structures determined by a specific experimental method.
        The search will return structures that were solved using the specified method.
        It returns the following json:
        key: pdb_ids: contains a list of PDB ids
        key: scores: the match score of the PDB w.r.t the query method (1.0 indicates exact match)
        key: total_count: total number of matches found
        key: returned_count: number of results returned (limited by limit parameter)
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "description": "Experimental method used to determine the structure. Example: 'X-RAY DIFFRACTION', 'ELECTRON MICROSCOPY', 'SOLUTION NMR'",
                    "enum": [
                        "X-RAY DIFFRACTION",
                        "ELECTRON MICROSCOPY",
                        "SOLUTION NMR",
                        "SOLID-STATE NMR",
                        "NEUTRON DIFFRACTION",
                        "ELECTRON CRYSTALLOGRAPHY",
                        "FIBER DIFFRACTION",
                    ],
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                },
            },
            "required": ["method", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

high_quality_structures_tool = {
    "type": "function",
    "function": {
        "name": "high_quality_structures",
        "description": """"
        You can search for high-quality X-ray crystallography structures based on resolution and R-work values.
        The search will return structures that meet the specified quality criteria.
        It returns the following json:
        key: pdb_ids: contains a list of PDB ids
        key: scores: the match score of the PDB (1.0 indicates meeting all quality criteria)
        key: total_count: total number of matches found
        key: returned_count: number of results returned (limited by limit parameter)
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "max_resolution": {
                    "type": "number",
                    "description": "Maximum resolution in Angstroms (lower is better)",
                    "minimum": 0.0,
                    "default": 2.0,
                },
                "max_r_work": {
                    "type": "number",
                    "description": "Maximum R-work value (lower is better)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.25,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                },
            },
            "required": ["max_resolution", "max_r_work", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

quality_filtered_sequence_search_tool = {
    "type": "function",
    "function": {
        "name": "quality_filtered_sequence_search",
        "description": """"
        Search for high-quality structures containing similar sequences.
        Combines sequence similarity search with structure quality filters.
        Perfect for researchers looking for reliable structural templates.
        Returns structures that match both sequence similarity and quality criteria.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "sequence": {
                    "type": "string",
                    "description": "Protein sequence in one-letter code",
                },
                "min_resolution": {
                    "type": "number",
                    "description": "Maximum acceptable resolution in Angstroms",
                    "default": 3.0,
                },
                "max_r_free": {
                    "type": "number",
                    "description": "Maximum acceptable R-free value",
                    "default": 0.3,
                },
                "sequence_identity_cutoff": {
                    "type": "number",
                    "description": "Minimum sequence identity (0.0-1.0)",
                    "default": 0.7,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                },
            },
            "required": ["sequence", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

ligand_protein_interaction_search_tool = {
    "type": "function",
    "function": {
        "name": "ligand_protein_interaction_search",
        "description": """"
        Search for structures containing specific protein-ligand interactions.
        Crucial for drug discovery and understanding molecular recognition.
        Returns structures containing similar ligand interactions with good resolution.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "ligand_smiles": {
                    "type": "string",
                    "description": "SMILES string of the ligand",
                },
                "ligand_name": {
                    "type": "string",
                    "description": "Common name or ID of the ligand",
                },
                "resolution_cutoff": {
                    "type": "number",
                    "description": "Maximum acceptable resolution",
                    "default": 2.5,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                },
            },
            "required": ["limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}


RCSB_SEARCH_API_TOOLS = [
    text_search_tool,
    sequence_search_tool,
    structure_search_tool,
    chemical_search_tool,
    organism_search_tool,
    method_search_tool,
    high_quality_structures_tool,
    quality_filtered_sequence_search_tool,
    ligand_protein_interaction_search_tool,
]

RCSB_SEARCH_API_TOOL_DESCRIPTIONS = {
    "text_search_tool": {
        "tool": text_search_tool,
        "desc": "Search PDB entries using text queries like protein names or PDB IDs.",
        "function": text_search
    },
    "sequence_search": {
        "tool": sequence_search_tool,
        "desc": "Find structures with similar amino acid or nucleotide sequences using BLAST-like algorithm.",
        "function": sequence_search
    },
    "structure_search_tool": {
        "tool": structure_search_tool,
        "desc": "Find structures with similar 3D shapes using a reference PDB structure.",
        "function": structure_search
    },
    "chemical_search_tool": {
        "tool": chemical_search_tool,
        "desc": "Find structures containing specific chemical compounds using SMILES or InChI identifiers.",
        "function": chemical_search
    },
    "organism_search_tool": {
        "tool": organism_search_tool,
        "desc": "Find structures from a specific organism using its scientific name.",
        "function": organism_search
    },
    "method_search_tool": {
        "tool": method_search_tool,
        "desc": "Find structures determined by a specific experimental method like X-ray or NMR.",
        "function": method_search
    },
    "high_quality_structures_tool": {
        "tool": high_quality_structures_tool,
        "desc": "Find high-quality X-ray structures based on resolution and R-work criteria.",
        "function": high_quality_structures
    },
    "quality_filtered_sequence_search_tool": {
        "tool": quality_filtered_sequence_search_tool,
        "desc": "Search for high-quality structures containing similar sequences with resolution and R-factor filters.",
        "function": quality_filtered_sequence_search
    },
    "ligand_protein_interaction_search_tool": {
        "tool": ligand_protein_interaction_search_tool,
        "desc": "Find structures containing specific protein-ligand interactions using SMILES or ligand names.",
        "function": ligand_protein_interaction_search
    }
}


class SearchAPIUnifiedResults(BaseModel):
    tool_used: str
    pdb_ids: list[str]
    total_count: int
    scores: dict[str, float]
    returned_count: int
    query_params: dict
   