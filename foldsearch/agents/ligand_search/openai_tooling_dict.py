"""
OpenAI Function Calling Schema Definitions for Ligand Search Tools

This module contains the OpenAI function calling schema definitions that enable
AI models to understand and invoke the ligand search tools. Each schema provides
detailed descriptions of tool capabilities, parameter requirements, and expected
return formats.

These schemas are essential for:
- AI agent integration with OpenAI GPT models
- Automatic tool selection and parameter extraction
- Dynamic query interpretation and execution planning
- Function calling workflows in conversational AI

The schemas follow OpenAI's function calling specification and include:
- Comprehensive tool descriptions for model understanding
- Detailed parameter schemas with types, constraints, and descriptions
- Required vs optional parameter specifications
- Input validation constraints and ranges
- Return format documentation

Each tool schema maps directly to a corresponding implementation function
in the tooling.py module, maintaining consistency between AI interface
and actual functionality.
"""

search_ligands_tool = {
    "type": "function",
    "function": {
        "name": "search_ligands",
        "description": """
        Comprehensive ligand search by name, SMILES, InChI, or molecular formula.
        
        This versatile search function supports multiple identifier types and matching
        strategies to find chemical compounds in major databases. It's the primary
        tool for initial ligand discovery and compound lookup operations.
        
        Search Types:
        - name: Common/trade names, IUPAC names, synonyms
        - smiles: SMILES chemical structure notation
        - inchi: InChI chemical identifier strings  
        - formula: Molecular formula (e.g., C8H10N4O2)
        - chembl_id: ChEMBL database identifiers (e.g., CHEMBL25)
        
        Matching Strategies:
        - exact_match=True: Precise identifier matching (faster, restrictive)
        - exact_match=False: Fuzzy/partial matching (slower, comprehensive)
        
        Returns JSON with:
        - ligands: list of found compounds
        - returned_count: number of results returned (limited by 'limit' parameter)
        - execution_time: search operation duration in seconds
        - search_metadata: query parameters and search context
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search terms (e.g., 'caffeine', 'CCO', 'C8H10N4O2', 'CHEMBL25')"
                },
                "search_type": {
                    "type": "string",
                    "enum": ["name", "smiles", "inchi", "formula", "chembl_id"],
                    "description": "Type of search to perform"
                },
                "exact_match": {
                    "type": "boolean",
                    "description": "Whether to perform exact matching"
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    }
}
