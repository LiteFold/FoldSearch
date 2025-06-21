import requests
from typing import Dict, List, Optional, Literal, Union
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# =============================================================================
# CONFIGURATION & UTILITIES
# =============================================================================

BASE_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
REST_BASE_URL = "https://data.rcsb.org/rest/v1/core"
GRAPHQL_URL = "https://data.rcsb.org/graphql"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3


def _make_request(
    query_data: Dict,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Optional[Dict]:
    """Make HTTP request with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                BASE_URL,
                json=query_data,
                timeout=timeout,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 204:
                return {"result_set": [], "total_count": 0}
            else:
                print(f"HTTP {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)

    return None


def _make_rest_request(url: str, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """Make REST API request with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
    return None


def _parse_search_results(response: Dict, limit: Optional[int] = None) -> Dict:
    """Parse API response to extract PDB IDs and scores"""
    if not response:
        return {"pdb_ids": [], "total_count": 0, "scores": {}}

    result_set = response.get("result_set", [])
    total_count = response.get("total_count", 0)

    pdb_ids = []
    scores = {}

    for result in result_set:
        pdb_id = result.get("identifier", "")
        score = result.get("score", 0)

        # Clean PDB ID (handle different formats)
        if "_" in pdb_id:
            pdb_id = pdb_id.split("_")[0]
        elif "." in pdb_id:
            pdb_id = pdb_id.split(".")[0]
        elif "-" in pdb_id:
            pdb_id = pdb_id.split("-")[0]

        if pdb_id and pdb_id not in scores:
            pdb_ids.append(pdb_id)
            scores[pdb_id] = score

    if limit and len(pdb_ids) > limit:
        pdb_ids = pdb_ids[:limit]
        scores = {k: v for k, v in scores.items() if k in pdb_ids}

    return {
        "pdb_ids": pdb_ids,
        "total_count": total_count,
        "scores": scores,
        "returned_count": len(pdb_ids),
    }


# =============================================================================
# CORE SEARCH TOOLS (10 COMPREHENSIVE FUNCTIONS)
# =============================================================================


def search_structures(
    query: str = None,
    organism: str = None,
    method: str = None,
    max_resolution: float = None,
    limit: int = 100,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Comprehensive structure search by text, organism, method, and quality filters.

    Args:
        query: Text search terms (e.g., "insulin", "HIV protease")
        organism: Scientific name (e.g., "Homo sapiens", "Escherichia coli")
        method: Experimental method ("X-RAY DIFFRACTION", "ELECTRON MICROSCOPY", "NMR")
        max_resolution: Maximum resolution in Angstroms
        limit: Maximum number of results
        timeout: Request timeout in seconds

    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    nodes = []
    
    if query:
        nodes.append({
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": query}
        })
    
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
    
    if not nodes:
        raise ValueError("At least one search parameter must be provided")
    
    if len(nodes) == 1:
        query_data = {
            "query": nodes[0],
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": min(limit, 10000)}}
        }
    else:
        query_data = {
            "query": {
                "type": "group",
                "logical_operator": "and",
                "nodes": nodes
            },
            "return_type": "entry", 
            "request_options": {"paginate": {"start": 0, "rows": min(limit, 10000)}}
        }



    response = _make_request(query_data, timeout)
    return _parse_search_results(response, limit)


def search_by_sequence(
    sequence: str,
    sequence_type: Literal["protein", "dna", "rna"] = "protein",
    identity_cutoff: float = 0.5,
    evalue_cutoff: float = 1.0,
    max_resolution: float = None,
    max_r_free: float = None,
    limit: int = 100,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Search for structures with similar sequences, optionally filtered by quality.

    Args:
        sequence: Amino acid or nucleotide sequence (one-letter code)
        sequence_type: Type of sequence
        identity_cutoff: Minimum sequence identity (0.0-1.0)
        evalue_cutoff: Maximum E-value threshold
        max_resolution: Maximum resolution filter (Angstroms)
        max_r_free: Maximum R-free value filter
        limit: Maximum number of results
        timeout: Request timeout in seconds

    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    nodes = [{
            "type": "terminal",
            "service": "sequence",
            "parameters": {
                "sequence_type": sequence_type,
                "value": sequence.upper(),
                "identity_cutoff": identity_cutoff,
            "evalue_cutoff": evalue_cutoff
        }
    }]
    
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
    
    if max_r_free:
        nodes.append({
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "refine.ls_R_factor_R_free",
                "operator": "less_or_equal",
                "value": max_r_free
            }
        })
    
    if len(nodes) == 1:
        query_data = {
            "query": nodes[0],
            "return_type": "entry",
            "request_options": {
                "scoring_strategy": "sequence",
                "sort": [{"sort_by": "score", "direction": "desc"}],
                "paginate": {"start": 0, "rows": min(limit, 10000)}
            }
        }
    else:
        query_data = {
            "query": {
                "type": "group",
                "logical_operator": "and",
                "nodes": nodes
            },
            "return_type": "entry",
            "request_options": {
                "scoring_strategy": "sequence",
                "sort": [{"sort_by": "score", "direction": "desc"}],
                "paginate": {"start": 0, "rows": min(limit, 10000)}
            }
        }


    response = _make_request(query_data, timeout)
    return _parse_search_results(response, limit)


def search_by_structure(
    reference_pdb_ids: Union[str, List[str]],
    assembly_id: str = "1",
    match_type: Literal["strict", "relaxed"] = "relaxed",
    limit: int = 100,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Search for structures with similar 3D shape to reference structure(s).

    Args:
        reference_pdb_ids: Single PDB ID or list of PDB IDs for comparison
        assembly_id: Assembly ID of reference structure
        match_type: Shape matching strictness
        limit: Maximum number of results per reference
        timeout: Request timeout in seconds

    Returns:
        Dict with combined results from all reference structures
    """
    if isinstance(reference_pdb_ids, str):
        reference_pdb_ids = [reference_pdb_ids]
    
    all_results = {"pdb_ids": [], "total_count": 0, "scores": {}, "by_reference": {}}
    
    for pdb_id in reference_pdb_ids:
        operator = "strict_shape_match" if match_type == "strict" else "relaxed_shape_match"

        query_data = {
            "query": {
                "type": "terminal",
                "service": "structure",
                "parameters": {
                    "value": {"entry_id": pdb_id.upper(), "assembly_id": assembly_id},
                    "operator": operator
                }
            },
            "return_type": "entry",
            "request_options": {
                "scoring_strategy": "structure",
                "paginate": {"start": 0, "rows": min(limit, 10000)}
            }
        }

        response = _make_request(query_data, timeout)
        result = _parse_search_results(response, limit)
        
        all_results["by_reference"][pdb_id] = result
        all_results["total_count"] += result["total_count"]
        
        # Merge unique results
        for new_pdb in result["pdb_ids"]:
            if new_pdb not in all_results["scores"]:
                all_results["pdb_ids"].append(new_pdb)
                all_results["scores"][new_pdb] = result["scores"][new_pdb]
    
    all_results["returned_count"] = len(all_results["pdb_ids"])
    return all_results


def search_by_chemical(
    identifier: str = None,
    identifier_type: Literal["SMILES", "InChI"] = "SMILES",
    ligand_name: str = None,
    match_type: str = "graph-relaxed",
    max_resolution: float = 2.5,
    limit: int = 100,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Search for structures containing specific chemical compounds or ligands.

    Args:
        identifier: SMILES string or InChI identifier
        identifier_type: Type of chemical identifier
        ligand_name: Common name or ID of the ligand
        match_type: Chemical matching algorithm
        max_resolution: Maximum resolution filter
        limit: Maximum number of results
        timeout: Request timeout in seconds

    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    nodes = []
    
    if identifier:
        nodes.append({
            "type": "terminal",
            "service": "chemical",
            "parameters": {
                "value": identifier,
                "type": "descriptor",
                "descriptor_type": identifier_type,
                "match_type": match_type
            }
        })
    
    if ligand_name:
        nodes.append({
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_nonpolymer_entity.pdbx_description",
                "operator": "contains_words",
                "value": ligand_name
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
    
    if not nodes:
        raise ValueError("Either identifier or ligand_name must be provided")
    
    if len(nodes) == 1:
        query_data = {
            "query": nodes[0],
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": min(limit, 10000)}}
        }
    else:
        query_data = {
            "query": {
                "type": "group",
                "logical_operator": "and",
                "nodes": nodes
            },
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": min(limit, 10000)}}
        }

    response = _make_request(query_data, timeout)
    return _parse_search_results(response, limit)


def get_high_quality_structures(
    max_resolution: float = 2.0,
    max_r_work: float = 0.25,
    max_r_free: float = 0.28,
    method: str = "X-RAY DIFFRACTION",
    min_year: int = 2000,
    limit: int = 100,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Search for high-quality structures with strict quality filters.

    Args:
        max_resolution: Maximum resolution in Angstroms
        max_r_work: Maximum R-work value
        max_r_free: Maximum R-free value
        method: Experimental method
        min_year: Minimum deposition year
        limit: Maximum number of results
        timeout: Request timeout in seconds

    Returns:
        Dict with pdb_ids, total_count, scores, returned_count
    """
    nodes = [
        {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "exptl.method",
                "operator": "exact_match",
                "value": method
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
        },
        {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "refine.ls_R_factor_R_free",
                "operator": "less_or_equal",
                "value": max_r_free
            }
        },
        {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_accession_info.initial_release_date",
                "operator": "greater_or_equal",
                "value": f"{min_year}-01-01"
            }
        }
    ]
    
    query_data = {
        "query": {
            "type": "group",
            "logical_operator": "and",
            "nodes": nodes
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": min(limit, 10000)},
            "sort": [{"sort_by": "rcsb_entry_info.resolution_combined", "direction": "asc"}]
        }
    }

    response = _make_request(query_data, timeout)
    return _parse_search_results(response, limit)


def get_structure_details(
    pdb_ids: Union[str, List[str]],
    include_assembly: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Get comprehensive structural details for one or multiple PDB entries.

    Args:
        pdb_ids: Single PDB ID or list of PDB IDs
        include_assembly: Whether to include assembly information
        timeout: Request timeout in seconds

    Returns:
        Dict with detailed information for each structure
    """
    if isinstance(pdb_ids, str):
        pdb_ids = [pdb_ids]
    
    results = {}
    
    def fetch_structure_info(pdb_id):
        info = {"pdb_id": pdb_id.upper()}
        
        # Get entry info
        entry_url = f"{REST_BASE_URL}/entry/{pdb_id.upper()}"
        entry_data = _make_rest_request(entry_url, timeout)
        
        if entry_data:
            rcsb_info = entry_data.get("rcsb_entry_info", {})
            refine = (entry_data.get("refine") or [{}])[0]
            
            info.update({
                "title": entry_data.get("struct", {}).get("title"),
                "method": (entry_data.get("exptl") or [{}])[0].get("method"),
                "resolution_A": refine.get("ls_dres_high"),
                "r_work": refine.get("ls_rfactor_rwork"),
                "r_free": refine.get("ls_rfactor_rfree"),
                "space_group": entry_data.get("symmetry", {}).get("space_group_name_hm"),
                "polymer_entity_count": rcsb_info.get("polymer_entity_count"),
                "ligands": rcsb_info.get("nonpolymer_bound_components", []),
                "deposition_date": rcsb_info.get("initial_release_date")
            })
        
        # Get polymer entities
        entities = []
        for entity_id in range(1, (info.get("polymer_entity_count", 0) or 0) + 1):
            entity_url = f"{REST_BASE_URL}/polymer_entity/{pdb_id.upper()}/{entity_id}"
            entity_data = _make_rest_request(entity_url, timeout)
            
            if entity_data:
                poly = entity_data.get("entity_poly", {})
                src = (entity_data.get("rcsb_entity_source_organism") or [{}])[0]
                names = entity_data.get("rcsb_polymer_entity", {})
                
                entities.append({
                    "entity_id": str(entity_id),
                    "description": names.get("pdbx_description"),
                    "sequence_length": poly.get("rcsb_sample_sequence_length"),
                    "molecule_type": poly.get("rcsb_entity_polymer_type"),
                    "organism": src.get("scientific_name"),
                    "chains": entity_data.get("rcsb_polymer_entity_container_identifiers", {}).get("asym_ids", [])
                })
        
        info["entities"] = entities
        
        # Get assembly info if requested
        if include_assembly:
            assembly_url = f"{REST_BASE_URL}/assembly/{pdb_id.upper()}/1"
            assembly_data = _make_rest_request(assembly_url, timeout)
            
            if assembly_data:
                asm_core = assembly_data.get("pdbx_struct_assembly", {})
                info["assembly"] = {
                    "oligomeric_state": asm_core.get("oligomeric_details"),
                    "oligomeric_count": asm_core.get("oligomeric_count"),
                    "method": asm_core.get("method_details")
                }
        
        return info
    
    # Use threading for multiple PDBs
    with ThreadPoolExecutor(max_workers=min(len(pdb_ids), 10)) as executor:
        future_to_pdb = {executor.submit(fetch_structure_info, pdb_id): pdb_id for pdb_id in pdb_ids}
        
        for future in as_completed(future_to_pdb):
            pdb_id = future_to_pdb[future]
            try:
                result = future.result()
                results[pdb_id.upper()] = result
            except Exception as e:
                results[pdb_id.upper()] = {"error": str(e)}
    
    return results


def get_sequences(
    pdb_ids: Union[str, List[str]],
    entity_ids: Union[str, List[str]] = "1",
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Get protein/nucleic acid sequences for one or multiple structures.
    
    Args:
        pdb_ids: Single PDB ID or list of PDB IDs
        entity_ids: Single entity ID or list of entity IDs (for each PDB)
        timeout: Request timeout in seconds
        
    Returns:
        Dict with sequences for each PDB/entity combination
    """
    if isinstance(pdb_ids, str):
        pdb_ids = [pdb_ids]
    if isinstance(entity_ids, str):
        entity_ids = [entity_ids] * len(pdb_ids)
    
    results = {}
    
    def fetch_sequence(pdb_id, entity_id):
        entity_url = f"{REST_BASE_URL}/polymer_entity/{pdb_id.upper()}/{entity_id}"
        entity_data = _make_rest_request(entity_url, timeout)
        
        if entity_data:
            poly = entity_data.get("entity_poly", {})
            return {
                "pdb_id": pdb_id.upper(),
                "entity_id": entity_id,
                "sequence": poly.get("pdbx_seq_one_letter_code_can"),
                "length": poly.get("rcsb_sample_sequence_length"),
                "type": poly.get("rcsb_entity_polymer_type")
            }
        return {"pdb_id": pdb_id.upper(), "entity_id": entity_id, "error": "Not found"}
    
    with ThreadPoolExecutor(max_workers=min(len(pdb_ids), 10)) as executor:
        futures = []
        for i, pdb_id in enumerate(pdb_ids):
            entity_id = entity_ids[i] if i < len(entity_ids) else "1"
            futures.append(executor.submit(fetch_sequence, pdb_id, entity_id))
        
        for future in as_completed(futures):
            result = future.result()
            key = f"{result['pdb_id']}_{result['entity_id']}"
            results[key] = result
    
    return results


def compare_structures(
    pdb_ids: List[str],
    comparison_type: Literal["sequence", "structure", "both"] = "both",
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Compare multiple structures by sequence identity and/or structural similarity.
    
    Args:
        pdb_ids: List of PDB IDs to compare
        comparison_type: Type of comparison to perform
        timeout: Request timeout in seconds
        
    Returns:
        Dict with pairwise comparison results
    """
    if len(pdb_ids) < 2:
        raise ValueError("At least 2 PDB IDs required for comparison")
    
    results = {
        "pdb_ids": pdb_ids,
        "comparisons": {},
        "summary": {}
    }
    
    # Get sequences for sequence comparison
    if comparison_type in ["sequence", "both"]:
        sequences = get_sequences(pdb_ids, timeout=timeout)
        
        # Simple sequence identity calculation (you might want to use proper alignment)
        for i, pdb1 in enumerate(pdb_ids):
            for pdb2 in pdb_ids[i+1:]:
                key1 = f"{pdb1.upper()}_1"
                key2 = f"{pdb2.upper()}_1"
                
                if key1 in sequences and key2 in sequences:
                    seq1 = sequences[key1].get("sequence", "")
                    seq2 = sequences[key2].get("sequence", "")

                    # Simple identity calculation (for demonstration)
                    if seq1 and seq2:
                        min_len = min(len(seq1), len(seq2))
                        matches = sum(1 for a, b in zip(seq1, seq2) if a == b)
                        identity = matches / min_len if min_len > 0 else 0
                        
                        pair_key = f"{pdb1}_{pdb2}"
                        results["comparisons"][pair_key] = {
                            "sequence_identity": round(identity, 3),
                            "length_difference": abs(len(seq1) - len(seq2))
                        }
    
    # Structure comparison would require more complex implementation
    # For now, providing framework
    if comparison_type in ["structure", "both"]:
        # This would require implementing structural alignment algorithms
        # or using external tools like PyMOL or ChimeraX APIs
        results["note"] = "Structural comparison requires additional implementation"
    
    return results


def analyze_interactions(
    pdb_ids: Union[str, List[str]],
    interaction_type: Literal["protein-protein", "protein-ligand", "all"] = "all",
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Analyze molecular interactions in structures.
    
    Args:
        pdb_ids: Single PDB ID or list of PDB IDs
        interaction_type: Type of interactions to analyze
        timeout: Request timeout in seconds
        
    Returns:
        Dict with interaction analysis for each structure
    """
    if isinstance(pdb_ids, str):
        pdb_ids = [pdb_ids]
    
    results = {}
    
    for pdb_id in pdb_ids:
        structure_info = get_structure_details(pdb_id, include_assembly=True, timeout=timeout)
        pdb_data = structure_info.get(pdb_id.upper(), {})
        
        interactions = {
            "pdb_id": pdb_id.upper(),
            "protein_chains": [],
            "ligands": [],
            "interactions": []
        }
        
        # Extract protein chains
        for entity in pdb_data.get("entities", []):
            if entity.get("molecule_type") == "protein":
                interactions["protein_chains"].extend(entity.get("chains", []))
        
        # Extract ligands
        interactions["ligands"] = pdb_data.get("ligands", [])
        
        # Analyze based on type
        if interaction_type in ["protein-protein", "all"]:
            if len(interactions["protein_chains"]) > 1:
                interactions["interactions"].append({
                    "type": "protein-protein",
                    "description": f"Multi-chain protein complex with {len(interactions['protein_chains'])} chains"
                })
        
        if interaction_type in ["protein-ligand", "all"]:
            if interactions["ligands"]:
                interactions["interactions"].append({
                    "type": "protein-ligand",
                    "ligand_count": len(interactions["ligands"]),
                    "ligands": interactions["ligands"]
                })
        
        # Assembly information
        assembly = pdb_data.get("assembly", {})
        if assembly:
            interactions["quaternary_structure"] = {
                "oligomeric_state": assembly.get("oligomeric_state"),
                "oligomeric_count": assembly.get("oligomeric_count")
            }
        
        results[pdb_id.upper()] = interactions
    
    return results


def get_structural_summary(
    pdb_ids: Union[str, List[str]],
    include_quality_metrics: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict:
    """
    Get comprehensive structural summary for research overview.
    
    Args:
        pdb_ids: Single PDB ID or list of PDB IDs
        include_quality_metrics: Whether to include detailed quality metrics
        timeout: Request timeout in seconds
        
    Returns:
        Dict with comprehensive summary for each structure
    """
    if isinstance(pdb_ids, str):
        pdb_ids = [pdb_ids]
    
    # Get detailed structure information
    details = get_structure_details(pdb_ids, include_assembly=True, timeout=timeout)
    
    summaries = {}
    
    for pdb_id in pdb_ids:
        pdb_data = details.get(pdb_id.upper(), {})
        
        if "error" in pdb_data:
            summaries[pdb_id.upper()] = pdb_data
            continue
        
        summary = {
            "pdb_id": pdb_id.upper(),
            "title": pdb_data.get("title"),
            "experimental": {
                "method": pdb_data.get("method"),
                "resolution_A": pdb_data.get("resolution_A"),
                "space_group": pdb_data.get("space_group"),
                "deposition_date": pdb_data.get("deposition_date")
            },
            "composition": {
                "protein_entities": len([e for e in pdb_data.get("entities", []) if e.get("molecule_type") == "protein"]),
                "total_entities": len(pdb_data.get("entities", [])),
                "ligands": len(pdb_data.get("ligands", [])),
                "unique_organisms": len(set(e.get("organism") for e in pdb_data.get("entities", []) if e.get("organism")))
            },
            "biological_assembly": pdb_data.get("assembly", {}),
            "research_relevance": {
                "has_ligands": len(pdb_data.get("ligands", [])) > 0,
                "is_complex": len(pdb_data.get("entities", [])) > 1,
                "high_resolution": (pdb_data.get("resolution_A") or 999) < 2.0
            }
        }
        
        if include_quality_metrics:
            summary["quality"] = {
                "resolution_A": pdb_data.get("resolution_A"),
                "r_work": pdb_data.get("r_work"),
                "r_free": pdb_data.get("r_free"),
                "quality_score": _calculate_quality_score(pdb_data)
            }
        
        # Add organism summary
        organisms = [e.get("organism") for e in pdb_data.get("entities", []) if e.get("organism")]
        if organisms:
            summary["organisms"] = list(set(organisms))
        
        summaries[pdb_id.upper()] = summary
    
    return summaries


def _calculate_quality_score(structure_data: Dict) -> str:
    """Calculate a simple quality score based on available metrics"""
    resolution = structure_data.get("resolution_A")
    r_work = structure_data.get("r_work")
    r_free = structure_data.get("r_free")
    
    score = 0
    factors = []
    
    if resolution:
        if resolution < 1.5:
            score += 3
            factors.append("excellent resolution")
        elif resolution < 2.0:
            score += 2
            factors.append("very good resolution")
        elif resolution < 2.5:
            score += 1
            factors.append("good resolution")
    
    if r_work and r_work < 0.2:
        score += 1
        factors.append("good R-work")
    
    if r_free and r_free < 0.25:
        score += 1
        factors.append("good R-free")
    
    if score >= 4:
        return f"Excellent ({', '.join(factors)})"
    elif score >= 2:
        return f"Good ({', '.join(factors)})"
    elif score >= 1:
        return f"Acceptable ({', '.join(factors)})"
    else:
        return "Limited quality data"



 
