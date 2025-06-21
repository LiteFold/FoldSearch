import requests
from typing import Dict, Optional, Literal
import time


BASE_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3

def _make_request(query_data: Dict, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """Make HTTP request with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                BASE_URL,
                json=query_data,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 204:
                # No results found
                return {"result_set": [], "total_count": 0}
            else:
                print(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                
    return None

def _parse_results(response: Dict, limit: Optional[int] = None) -> Dict:
    """Parse API response to extract useful information"""
    if not response:
        return {"pdb_ids": [], "total_count": 0, "scores": {}}
        
    result_set = response.get("result_set", [])
    total_count = response.get("total_count", 0)
    
    pdb_ids = []
    scores = {}
    
    # Extract PDB IDs and scores
    for result in result_set:
        pdb_id = result.get("identifier", "")
        score = result.get("score", 0)
        
        # Handle different return types (entry, polymer_entity, assembly, etc.)
        if "_" in pdb_id:  # polymer_entity format like "4HHB_1"
            pdb_id = pdb_id.split("_")[0]
        elif "." in pdb_id:  # instance format like "4HHB.A"  
            pdb_id = pdb_id.split(".")[0]
        elif "-" in pdb_id:  # assembly format like "4HHB-1"
            pdb_id = pdb_id.split("-")[0]
            
        if pdb_id and pdb_id not in scores:  # Avoid duplicates
            pdb_ids.append(pdb_id)
            scores[pdb_id] = score
            
    # Apply limit if specified
    if limit and len(pdb_ids) > limit:
        pdb_ids = pdb_ids[:limit]
        scores = {k: v for k, v in scores.items() if k in pdb_ids}
        
    return {
        "pdb_ids": pdb_ids,
        "total_count": total_count,
        "scores": scores,
        "returned_count": len(pdb_ids)
    }

# ===== BASIC SEARCH FUNCTIONS =====

def text_search(query: str, limit: int = 100, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Full-text search across all PDB annotations
    
    Args:
        query: Search terms (e.g., "insulin", "HIV protease")
        limit: Maximum number of results to return
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    query_data = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {
                "value": query
            }
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": min(limit, 10000)}
        }
    }
    
    response = _make_request(query_data, timeout, max_retries)
    return _parse_results(response, limit)

def sequence_search(sequence: str, sequence_type: Literal["protein", "dna", "rna"] = "protein", 
                   identity_cutoff: float = 0.5, evalue_cutoff: float = 1.0, limit: int = 100,
                   timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for similar sequences using BLAST-like algorithm
    
    Args:
        sequence: Amino acid or nucleotide sequence (one-letter code)
        sequence_type: Type of sequence ("protein", "dna", "rna")
        identity_cutoff: Minimum sequence identity (0.0-1.0)
        evalue_cutoff: Maximum E-value threshold
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    query_data = {
        "query": {
            "type": "terminal",
            "service": "sequence",
            "parameters": {
                "sequence_type": sequence_type,
                "value": sequence.upper(),
                "identity_cutoff": identity_cutoff,
                "evalue_cutoff": evalue_cutoff
            }
        },
        "return_type": "polymer_entity",
        "request_options": {
            "scoring_strategy": "sequence",
            "paginate": {"start": 0, "rows": min(limit, 10000)}
        }
    }
    
    response = _make_request(query_data, timeout, max_retries)
    return _parse_results(response, limit)

def structure_search(pdb_id: str, assembly_id: str = "1", 
                    match_type: Literal["strict", "relaxed"] = "relaxed", limit: int = 100,
                    timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for structures with similar 3D shape
    
    Args:
        pdb_id: Reference PDB ID for shape comparison
        assembly_id: Assembly ID of reference structure
        match_type: "strict" or "relaxed" shape matching
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    operator = "strict_shape_match" if match_type == "strict" else "relaxed_shape_match"
    
    query_data = {
        "query": {
            "type": "terminal",
            "service": "structure",
            "parameters": {
                "value": {
                    "entry_id": pdb_id.upper(),
                    "assembly_id": assembly_id
                },
                "operator": operator
            }
        },
        "return_type": "entry",
        "request_options": {
            "scoring_strategy": "structure",
            "paginate": {"start": 0, "rows": min(limit, 10000)}
        }
    }
    
    response = _make_request(query_data, timeout, max_retries)
    return _parse_results(response, limit)

def chemical_search(identifier: str, identifier_type: Literal["SMILES", "InChI"] = "SMILES",
                   match_type: str = "graph-relaxed", limit: int = 100,
                   timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for chemically similar compounds
    
    Args:
        identifier: SMILES string or InChI identifier
        identifier_type: Type of chemical identifier
        match_type: Chemical matching algorithm
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    query_data = {
        "query": {
            "type": "terminal",
            "service": "chemical",
            "parameters": {
                "value": identifier,
                "type": "descriptor",
                "descriptor_type": identifier_type,
                "match_type": match_type
            }
        },
        "return_type": "entry",
        "request_options": {
            "scoring_strategy": "chemical",
            "paginate": {"start": 0, "rows": min(limit, 10000)}
        }
    }
    
    response = _make_request(query_data, timeout, max_retries)
    return _parse_results(response, limit)

# ===== ATTRIBUTE-BASED SEARCHES =====

def organism_search(organism: str, limit: int = 100, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search structures by source organism
    
    Args:
        organism: Scientific name (e.g., "Homo sapiens", "Escherichia coli")
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    query_data = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_entity_source_organism.taxonomy_lineage.name",
                "operator": "exact_match",
                "value": organism
            }
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": min(limit, 10000)}
        }
    }
    
    response = _make_request(query_data, timeout, max_retries)
    return _parse_results(response, limit)

def method_search(method: str, limit: int = 100, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search structures by experimental method
    
    Args:
        method: Experimental method (e.g., "X-RAY DIFFRACTION", "ELECTRON MICROSCOPY", "NMR")
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    query_data = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "exptl.method",
                "operator": "exact_match",
                "value": method
            }
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": min(limit, 10000)}
        }
    }
    
    response = _make_request(query_data, timeout, max_retries)
    return _parse_results(response, limit)

def resolution_search(max_resolution: float, min_resolution: float = 0.0, limit: int = 100,
                     timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search structures by resolution range
    
    Args:
        max_resolution: Maximum resolution in Angstroms
        min_resolution: Minimum resolution in Angstroms
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    query_data = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_entry_info.resolution_combined",
                "operator": "range",
                "value": {
                    "from": min_resolution,
                    "to": max_resolution,
                    "include_lower": True,
                    "include_upper": True
                }
            }
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": min(limit, 10000)},
            "sort": [{"sort_by": "rcsb_entry_info.resolution_combined", "direction": "asc"}]
        }
    }
    
    response = _make_request(query_data, timeout, max_retries)
    return _parse_results(response, limit)

# ===== ADVANCED SEARCHES =====

def high_quality_structures(max_resolution: float = 2.0, max_r_work: float = 0.25, limit: int = 100,
                           timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for high-quality X-ray structures
    
    Args:
        max_resolution: Maximum resolution in Angstroms
        max_r_work: Maximum R-work value
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    query_data = {
        "query": {
            "type": "group",
            "logical_operator": "and",
            "nodes": [
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "exptl.method",
                        "operator": "exact_match",
                        "value": "X-RAY DIFFRACTION"
                    }
                },
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_entry_info.resolution_combined",
                        "operator": "less_or_equal",
                        "value": max_resolution
                    }
                },
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "refine.ls_R_factor_R_work",
                        "operator": "less_or_equal",
                        "value": max_r_work
                    }
                }
            ]
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": min(limit, 10000)},
            "sort": [{"sort_by": "rcsb_entry_info.resolution_combined", "direction": "asc"}]
        }
    }
    
    response = _make_request(query_data, timeout, max_retries)
    return _parse_results(response, limit)

def membrane_proteins(limit: int = 100, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for membrane proteins annotated by external resources
    
    Args:
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    query_data = {
        "query": {
            "type": "group",
            "logical_operator": "or",
            "nodes": [
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_polymer_entity_annotation.type",
                        "operator": "exact_match",
                        "value": "PDBTM"
                    }
                },
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_polymer_entity_annotation.type",
                        "operator": "exact_match",
                        "value": "OPM"
                    }
                },
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_polymer_entity_annotation.type",
                        "operator": "exact_match",
                        "value": "mpstruc"
                    }
                }
            ]
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": min(limit, 10000)}
        }
    }
    
    response = _make_request(query_data, timeout, max_retries)
    return _parse_results(response, limit)

def complex_search(text_query: str, organism: str = None, method: str = None, 
                  max_resolution: float = None, limit: int = 100,
                  timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Combined search with multiple criteria using AND logic
    
    Args:
        text_query: Text search terms
        organism: Source organism (optional)
        method: Experimental method (optional)  
        max_resolution: Maximum resolution in Angstroms (optional)
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    nodes = [
        {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": text_query}
        }
    ]
    
    if organism:
        nodes.append({
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_entity_source_organism.taxonomy_lineage.name",
                "operator": "exact_match",
                "value": organism
            }
        })
    
    if method:
        nodes.append({
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "exptl.method",
                "operator": "exact_match",
                "value": method
            }
        })
    
    if max_resolution:
        nodes.append({
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_entry_info.resolution_combined",
                "operator": "less_or_equal",
                "value": max_resolution
            }
        })
    
    query_data = {
        "query": {
            "type": "group",
            "logical_operator": "and",
            "nodes": nodes
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": min(limit, 10000)}
        }
    }
    
    response = _make_request(query_data, timeout, max_retries)
    return _parse_results(response, limit)

# ===== UTILITY FUNCTIONS =====

def get_summary_stats(timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Get summary statistics about the PDB archive
    
    Args:
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dict with basic PDB statistics
    """
    # Total structures
    total_query = {
        "query": {"type": "terminal", "service": "text"},
        "return_type": "entry",
        "request_options": {"return_counts": True}
    }
    
    # X-ray structures
    xray_query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "exptl.method",
                "operator": "exact_match",
                "value": "X-RAY DIFFRACTION"
            }
        },
        "return_type": "entry",
        "request_options": {"return_counts": True}
    }
    
    # NMR structures  
    nmr_query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "exptl.method",
                "operator": "exact_match",
                "value": "SOLUTION NMR"
            }
        },
        "return_type": "entry",
        "request_options": {"return_counts": True}
    }
    
    # EM structures
    em_query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "exptl.method",
                "operator": "exact_match",
                "value": "ELECTRON MICROSCOPY"
            }
        },
        "return_type": "entry",
        "request_options": {"return_counts": True}
    }
    
    total_count = _make_request(total_query, timeout, max_retries).get("total_count", 0)
    xray_count = _make_request(xray_query, timeout, max_retries).get("total_count", 0)
    nmr_count = _make_request(nmr_query, timeout, max_retries).get("total_count", 0)
    em_count = _make_request(em_query, timeout, max_retries).get("total_count", 0)
    
    return {
        "total_structures": total_count,
        "xray_structures": xray_count,
        "nmr_structures": nmr_count,
        "em_structures": em_count,
        "other_structures": total_count - xray_count - nmr_count - em_count
    } 