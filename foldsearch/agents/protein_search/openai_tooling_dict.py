search_structures_tool = {
    "type": "function",
    "function": {
        "name": "search_structures",
        "description": """
        Comprehensive structure search by text, organism, method, and quality filters.
        Returns structures matching the specified criteria with relevance scores.
        Returns JSON with:
        - pdb_ids: list of PDB IDs
        - scores: match scores for each PDB ID
        - total_count: total number of matches found
        - returned_count: number of results returned
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text search terms (e.g., 'insulin', 'HIV protease')"
                },
                "organism": {
                    "type": "string",
                    "description": "Scientific name (e.g., 'Homo sapiens', 'Escherichia coli')"
                },
                "method": {
                    "type": "string",
                    "description": "Experimental method ('X-RAY DIFFRACTION', 'ELECTRON MICROSCOPY', 'NMR')"
                },
                "max_resolution": {
                    "type": "number",
                    "description": "Maximum resolution in Angstroms"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "minimum": 1,
                    "maximum": 10000
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "minimum": 1
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    }
}

search_by_sequence_tool = {
    "type": "function",
    "function": {
        "name": "search_by_sequence",
        "description": """
        Search for structures with similar sequences, optionally filtered by quality.
        Performs sequence similarity search using BLAST-like algorithms.
        Returns JSON with:
        - pdb_ids: list of PDB IDs with similar sequences
        - scores: sequence similarity scores
        - total_count: total number of matches found
        - returned_count: number of results returned
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "sequence": {
                    "type": "string",
                    "description": "Amino acid or nucleotide sequence (one-letter code)"
                },
                "sequence_type": {
                    "type": "string",
                    "enum": ["protein", "dna", "rna"],
                    "description": "Type of sequence"
                },
                "identity_cutoff": {
                    "type": "number",
                    "description": "Minimum sequence identity (0.0-1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "evalue_cutoff": {
                    "type": "number",
                    "description": "Maximum E-value threshold",
                    "minimum": 0.0
                },
                "max_resolution": {
                    "type": "number",
                    "description": "Maximum resolution filter (Angstroms)"
                },
                "max_r_free": {
                    "type": "number",
                    "description": "Maximum R-free value filter"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "minimum": 1,
                    "maximum": 10000
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "minimum": 1
                }
            },
            "required": ["sequence"],
            "additionalProperties": False
        }
    }
}

search_by_structure_tool = {
    "type": "function",
    "function": {
        "name": "search_by_structure",
        "description": """
        Search for structures with similar 3D shape to reference structure(s).
        Performs structural similarity search based on 3D coordinates.
        Returns JSON with:
        - pdb_ids: list of structurally similar PDB IDs
        - scores: structural similarity scores
        - total_count: total number of matches found
        - by_reference: results organized by reference structure
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "reference_pdb_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of PDB IDs for comparison (or single PDB ID as string)"
                },
                "assembly_id": {
                    "type": "string",
                    "description": "Assembly ID of reference structure"
                },
                "match_type": {
                    "type": "string",
                    "enum": ["strict", "relaxed"],
                    "description": "Shape matching strictness"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results per reference",
                    "minimum": 1,
                    "maximum": 10000
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "minimum": 1
                }
            },
            "required": ["reference_pdb_ids"],
            "additionalProperties": False
        }
    }
}

search_by_chemical_tool = {
    "type": "function",
    "function": {
        "name": "search_by_chemical",
        "description": """
        Search for structures containing specific chemical compounds or ligands.
        Can search by SMILES, InChI, or ligand name.
        Returns JSON with:
        - pdb_ids: list of PDB IDs containing the chemical
        - scores: chemical match scores
        - total_count: total number of matches found
        - returned_count: number of results returned
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "SMILES string or InChI identifier"
                },
                "identifier_type": {
                    "type": "string",
                    "enum": ["SMILES", "InChI"],
                    "description": "Type of chemical identifier"
                },
                "ligand_name": {
                    "type": "string",
                    "description": "Common name or ID of the ligand"
                },
                "match_type": {
                    "type": "string",
                    "description": "Chemical matching algorithm",
                    "enum": ["graph-strict", "graph-relaxed", "fingerprint-tanimoto"]
                },
                "max_resolution": {
                    "type": "number",
                    "description": "Maximum resolution filter (Angstroms)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "minimum": 1,
                    "maximum": 10000
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "minimum": 1
                }
            },
            "required": ["identifier"],
            "additionalProperties": False
        }
    }
}

get_high_quality_structures_tool = {
    "type": "function",
    "function": {
        "name": "get_high_quality_structures",
        "description": """
        Search for high-quality structures with strict quality filters.
        Filters by resolution, R-factors, method, and deposition year.
        Returns JSON with:
        - pdb_ids: list of high-quality PDB IDs
        - scores: quality-based scores
        - total_count: total number of matches found
        - returned_count: number of results returned
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "max_resolution": {
                    "type": "number",
                    "description": "Maximum resolution in Angstroms"
                },
                "max_r_work": {
                    "type": "number",
                    "description": "Maximum R-work value"
                },
                "max_r_free": {
                    "type": "number",
                    "description": "Maximum R-free value"
                },
                "method": {
                    "type": "string",
                    "description": "Experimental method",
                    "enum": ["X-RAY DIFFRACTION", "ELECTRON MICROSCOPY", "NMR", "NEUTRON DIFFRACTION"]
                },
                "min_year": {
                    "type": "integer",
                    "description": "Minimum deposition year",
                    "minimum": 1970
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "minimum": 1,
                    "maximum": 10000
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "minimum": 1
                }
            },
            "required": [],
            "additionalProperties": False
        }
    }
}

get_structure_details_tool = {
    "type": "function",
    "function": {
        "name": "get_structure_details",
        "description": """
        Get comprehensive structural details for one or multiple PDB entries.
        Returns detailed information including experimental conditions, entities, and quality metrics.
        Returns JSON with detailed information for each structure including:
        - Basic info (title, method, resolution)
        - Quality metrics (R-work, R-free)
        - Entities (protein chains, ligands)
        - Assembly information
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "pdb_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of PDB IDs (or single PDB ID as string)"
                },
                "include_assembly": {
                    "type": "boolean",
                    "description": "Whether to include assembly information"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "minimum": 1
                }
            },
            "required": ["pdb_ids"],
            "additionalProperties": False
        }
    }
}

get_sequences_tool = {
    "type": "function",
    "function": {
        "name": "get_sequences",
        "description": """
        Get protein/nucleic acid sequences for one or multiple structures.
        Returns amino acid or nucleotide sequences for specified entities.
        Returns JSON with sequences for each PDB/entity combination including:
        - sequence: one-letter code sequence
        - length: sequence length
        - type: polymer type (protein, DNA, RNA)
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "pdb_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of PDB IDs (or single PDB ID as string)"
                },
                "entity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of entity IDs (or single entity ID as string)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "minimum": 1
                }
            },
            "required": ["pdb_ids"],
            "additionalProperties": False
        }
    }
}

compare_structures_tool = {
    "type": "function",
    "function": {
        "name": "compare_structures",
        "description": """
        Compare multiple structures by sequence identity and/or structural similarity.
        Performs pairwise comparisons between all provided structures.
        Returns JSON with:
        - pdb_ids: list of compared structures
        - comparisons: pairwise comparison results
        - summary: overall comparison summary
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "pdb_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of PDB IDs to compare (minimum 2)"
                },
                "comparison_type": {
                    "type": "string",
                    "enum": ["sequence", "structure", "both"],
                    "description": "Type of comparison to perform"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "minimum": 1
                }
            },
            "required": ["pdb_ids"],
            "additionalProperties": False
        }
    }
}

analyze_interactions_tool = {
    "type": "function",
    "function": {
        "name": "analyze_interactions",
        "description": """
        Analyze molecular interactions in structures.
        Identifies protein-protein, protein-ligand, and other molecular interactions.
        Returns JSON with:
        - protein_chains: list of protein chains
        - ligands: list of bound ligands
        - interactions: identified interaction types
        - quaternary_structure: assembly information
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "pdb_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of PDB IDs (or single PDB ID as string)"
                },
                "interaction_type": {
                    "type": "string",
                    "enum": ["protein-protein", "protein-ligand", "all"],
                    "description": "Type of interactions to analyze"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "minimum": 1
                }
            },
            "required": ["pdb_ids"],
            "additionalProperties": False
        }
    }
}

get_structural_summary_tool = {
    "type": "function",
    "function": {
        "name": "get_structural_summary",
        "description": """
        Get comprehensive structural summary for research overview.
        Provides a high-level summary of structural characteristics, quality, and research relevance.
        Returns JSON with:
        - Basic information (title, method, resolution)
        - Composition (entities, ligands, organisms)
        - Quality metrics and assessment
        - Research relevance indicators
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "pdb_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of PDB IDs (or single PDB ID as string)"
                },
                "include_quality_metrics": {
                    "type": "boolean",
                    "description": "Whether to include detailed quality metrics"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "minimum": 1
                }
            },
            "required": ["pdb_ids"],
            "additionalProperties": False
        }
    }
}

