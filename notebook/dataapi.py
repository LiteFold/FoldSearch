import requests
from typing import Dict, List, Optional
import time

# ===== CONSTANTS =====
REST_BASE_URL = "https://data.rcsb.org/rest/v1/core"
GRAPHQL_URL = "https://data.rcsb.org/graphql"
HOLDINGS_URL = "https://data.rcsb.org/rest/v1/holdings/current/entry_ids"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3

# ===== UTILITY FUNCTIONS =====

def _make_request_data(url: str, params: Dict = None, json_data: Dict = None, method: str = "GET", 
                 timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """
    Make HTTP request with retry logic and error handling
    """
    for attempt in range(max_retries):
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=json_data, timeout=timeout)
            else:
                response = requests.get(url, params=params, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"Resource not found: {url}")
                return None
            else:
                print(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                
    return None

# ===== REST API FUNCTIONS =====

def get_entry_info(pdb_id: str, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """
    Get entry information for a PDB structure
    
    Args:
        pdb_id: PDB identifier
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary containing entry information
    """
    url = f"{REST_BASE_URL}/entry/{pdb_id.upper()}"
    entry = _make_request_data(url, timeout=timeout, max_retries=max_retries)

    if not entry:
        return None

    rcsb_info   = entry.get("rcsb_entry_info", {})
    refine      = (entry.get("refine")          or [{}])[0]
    refine_hist = (entry.get("refine_hist")     or [{}])[0]
    geo_sum     = (entry.get("pdbx_vrpt_summary_geometry") or [{}])[0]

    summary = {
    # ── Experimental & structural data ──────────────────────────────
    "pdb_id"          : entry.get("entry", {}).get("id"),
    "title"           : entry.get("struct", {}).get("title"),
    "method"          : (entry.get("exptl") or [{}])[0].get("method"),
    "resolution_Å"    : refine.get("ls_dres_high"),          # 2.8
    "r_work"          : refine.get("ls_rfactor_rwork",       # 0.154
                                   refine.get("ls_rfactor_obs")),
    "atom_counts"     : {
        "total"   : rcsb_info.get("deposited_atom_count"),
        "protein" : refine_hist.get("pdbx_number_atoms_protein"),
        "ligand"  : refine_hist.get("pdbx_number_atoms_ligand"),
        "solvent" : refine_hist.get("number_atoms_solvent"),
    },
    "ligands"         : rcsb_info.get("nonpolymer_bound_components", []),
    "model_count"     : rcsb_info.get("deposited_model_count"),

    # ── Macromolecular content ──────────────────────────────────────
    "polymer_composition"    : rcsb_info.get("polymer_composition"),
    "polymer_entity_count"   : rcsb_info.get("polymer_entity_count"),
    "chain_count"            : rcsb_info.get("deposited_polymer_entity_instance_count"),
    "nonpolymer_entity_count": rcsb_info.get("nonpolymer_entity_count"),

    # ── Crystallography ─────────────────────────────────────────────
    "space_group" : entry.get("symmetry", {}).get("space_group_name_hm"),
    "unit_cell"   : {
        "a"     : entry.get("cell", {}).get("length_a"),
        "b"     : entry.get("cell", {}).get("length_b"),
        "c"     : entry.get("cell", {}).get("length_c"),
        "alpha" : entry.get("cell", {}).get("angle_alpha"),
        "beta"  : entry.get("cell", {}).get("angle_beta"),
        "gamma" : entry.get("cell", {}).get("angle_gamma"),
    },

    # ── Refinement / validation ────────────────────────────────────
    "refinement" : {
        "software"               : ", ".join(
            s["name"] for s in entry.get("software", [])
            if s.get("classification") == "refinement"
        ),
        "rmsd_bonds"             : geo_sum.get("bonds_rmsz"),
        "rmsd_angles"            : geo_sum.get("angles_rmsz"),
        "ramachandran_outliers%" : geo_sum.get("percent_ramachandran_outliers"),
        "rotamer_outliers%"      : geo_sum.get("percent_rotamer_outliers"),
        "clashscore"             : geo_sum.get("clashscore"),
    },
}
    return summary

def get_polymer_entity(pdb_id: str, entity_id: str, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """
    Get polymer entity information (protein, DNA, RNA)
    
    Args:
        pdb_id: PDB identifier
        entity_id: Entity identifier (usually numeric string)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary containing polymer entity information
    """
    url = f"{REST_BASE_URL}/polymer_entity/{pdb_id.upper()}/{entity_id}"
    entity = _make_request_data(url, timeout=timeout, max_retries=max_retries)
    
    if not entity:
        return None
    
    # Shorthands
    poly   = entity.get("entity_poly", {})
    src    = (entity.get("rcsb_entity_source_organism") or [{}])[0]
    names  = entity.get("rcsb_polymer_entity", {})
    ids    = entity.get("rcsb_polymer_entity_container_identifiers", {})
    annos  = entity.get("rcsb_polymer_entity_annotation", [])
    clust  = entity.get("rcsb_cluster_membership", [])

    # --- Annotation helpers -------------------------------------------
    def _collect(ids_of_type):
        return sorted(
            {a["annotation_id"] for a in annos if a["type"] in ids_of_type}
        )

    def _clusters_dict():
        # turn [{'cluster_id': 29374, 'identity': 100}, …] into {"100%": 29374, …}
        d = {}
        for c in clust:
            pct = f'{c["identity"]}%'
            d[pct] = c["cluster_id"]
        return d

    return {
        "pdb_id"       : ids.get("entry_id"),
        "entity_id"    : ids.get("entity_id"),
        "description"  : names.get("pdbx_description")
                        or names.get("rcsb_macromolecular_names_combined", [{}])[0].get("name"),
        "sequence"     : {
            "one_letter_code" : poly.get("pdbx_seq_one_letter_code_can"),
            "length"          : poly.get("rcsb_sample_sequence_length")
        },
        "chains"       : ids.get("asym_ids", []),            # e.g. ["A", "C"]
        "molecule_type": poly.get("rcsb_entity_polymer_type"),
        "molecular_weight_kDa": names.get("formula_weight"), # already in kDa
        "organism"     : {
            "scientific_name" : src.get("scientific_name"),
            "common_name"     : src.get("common_name"),
            "taxonomy_id"     : src.get("ncbi_taxonomy_id")
        },
        "uniprot_ids"  : ids.get("uniprot_ids", []),
        "annotations"  : {
            "pfam"     : _collect({"Pfam"}),
            "interpro" : _collect({"InterPro"}),
            "go"       : _collect({"GO"})
        },
        "homology_clusters" : _clusters_dict()               # 100 %, 95 %, 90 % …
    }

def get_assembly(pdb_id: str, assembly_id: str = "1", timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """
    Get biological assembly information
    
    Args:
        pdb_id: PDB identifier
        assembly_id: Assembly identifier (default: "1")
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary containing assembly information
    """
    url = f"{REST_BASE_URL}/assembly/{pdb_id.upper()}/{assembly_id}"
    asm = _make_request_data(url, timeout=timeout, max_retries=max_retries)
    
    if not asm:
        return None
    
    asm_core   = asm.get("pdbx_struct_assembly", {})
    asm_gen    = (asm.get("pdbx_struct_assembly_gen") or [{}])[0]
    asm_info   = asm.get("rcsb_assembly_info", {})
    symmetry   = asm.get("rcsb_struct_symmetry", [])

    return {
        # ── Top-level identity & composition ───────────────────────────
        "assembly_id"        : asm_core.get("id"),
        "oligomeric_state"   : asm_core.get("oligomeric_details"),   # e.g. "tetrameric"
        "oligomeric_count"   : asm_core.get("oligomeric_count"),     # 4
        "polymer_composition": asm_info.get("polymer_composition"),  # "heteromeric protein"
        "polymer_chains"     : asm_gen.get("asym_id_list", []),      # ['A','B','C','D',…]
        
        # ── How the assembly was defined ──────────────────────────────
        "defined_by"         : asm_core.get("method_details"),       # "PISA"
        
        # ── Symmetry summary (global) ─────────────────────────────────
        "symmetry" : [
            {
                "symbol"          : s.get("symbol"),                 # C2, D2 …
                "type"            : s.get("type"),                   # Cyclic / Dihedral
                "stoichiometry"   : s.get("stoichiometry"),          # ['A2','B2'] etc.
                "oligomeric_state": s.get("oligomeric_state")        # "Hetero 4-mer"
            }
            for s in symmetry
        ],
        
        # ── Interface / surface metrics ───────────────────────────────
        "num_interfaces"               : asm_info.get("num_interfaces"),
        "total_buried_surface_area_Å2" : asm_info.get("total_assembly_buried_surface_area"),
        "num_interface_residues"       : asm_info.get("total_number_interface_residues")
    }

# ===== GraphQL API FUNCTIONS =====

def graphql_query(query: str, variables: Dict = None, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """
    Execute GraphQL query
    
    Args:
        query: GraphQL query string
        variables: Optional variables for the query
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        GraphQL response data
    """
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
        
    response = _make_request_data(GRAPHQL_URL, json_data=payload, method="POST", timeout=timeout, max_retries=max_retries)
    
    if response and "errors" in response:
        print("GraphQL Errors:")
        for error in response["errors"]:
            print(f"  - {error['message']}")
    
    return response.get("data") if response else None

def get_entries_batch(pdb_ids: List[str], fields: List[str] = None, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """
    Get information for multiple entries in a single GraphQL query
    
    Args:
        pdb_ids: List of PDB identifiers
        fields: List of fields to retrieve (default: basic info)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary containing batch entry information
    """
    if fields is None:
        fields = ["rcsb_id", "struct { title }", "exptl { method }"]
    
    fields_str = " ".join(fields)
    pdb_ids_str = '", "'.join([pdb_id.upper() for pdb_id in pdb_ids])
    
    query = f"""
    {{
        entries(entry_ids: ["{pdb_ids_str}"]) {{
            {fields_str}
        }}
    }}
    """
    
    return graphql_query(query, timeout=timeout, max_retries=max_retries)

def get_polymer_entities_batch(entity_ids: List[str], fields: List[str] = None, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """
    Get polymer entity information for multiple entities
    
    Args:
        entity_ids: List of entity identifiers in format "PDB_ID_ENTITY_ID" (e.g., ["4HHB_1", "4HHB_2"])
        fields: List of fields to retrieve
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary containing batch entity information
    """
    if fields is None:
        fields = [
            "rcsb_id",
            "rcsb_entity_source_organism { ncbi_scientific_name }",
            "entity_poly { pdbx_seq_one_letter_code }"
        ]
    
    fields_str = " ".join(fields)
    entity_ids_str = '", "'.join(entity_ids)
    
    query = f"""
    {{
        polymer_entities(entity_ids: ["{entity_ids_str}"]) {{
            {fields_str}
        }}
    }}
    """
    
    return graphql_query(query, timeout=timeout, max_retries=max_retries)

# ===== SPECIALIZED QUERY FUNCTIONS =====

def get_sequence(pdb_id: str, entity_id: str = "1", timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[str]:
    """
    Get protein/nucleic acid sequence
    
    Args:
        pdb_id: PDB identifier
        entity_id: Entity identifier
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Sequence string in one-letter code
    """
    query = f"""
    {{
        polymer_entity(entry_id: "{pdb_id.upper()}", entity_id: "{entity_id}") {{
            entity_poly {{
                pdbx_seq_one_letter_code
            }}
        }}
    }}
    """
    
    result = graphql_query(query, timeout=timeout, max_retries=max_retries)
    if result and result.get("polymer_entity") and result["polymer_entity"].get("entity_poly"):
        return result["polymer_entity"]["entity_poly"]["pdbx_seq_one_letter_code"]
    return None

def get_organism_info(pdb_id: str, entity_id: str = "1", timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """
    Get organism information for a polymer entity
    
    Args:
        pdb_id: PDB identifier
        entity_id: Entity identifier
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary with organism information
    """
    query = f"""
    {{
        polymer_entity(entry_id: "{pdb_id.upper()}", entity_id: "{entity_id}") {{
            rcsb_entity_source_organism {{
                ncbi_taxonomy_id
                ncbi_scientific_name
                ncbi_parent_scientific_name
            }}
        }}
    }}
    """
    
    result = graphql_query(query, timeout=timeout, max_retries=max_retries)
    if result and result.get("polymer_entity"):
        return result["polymer_entity"].get("rcsb_entity_source_organism")
    return None

def get_structure_quality(pdb_id: str, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """
    Get structure quality metrics (resolution, R-factors, etc.)
    
    Args:
        pdb_id: PDB identifier
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary with quality metrics
    """
    query = f"""
    {{
        entry(entry_id: "{pdb_id.upper()}") {{
            rcsb_entry_info {{
                resolution_combined
                diffrn_resolution_high
            }}
            refine {{
                ls_d_res_high
                ls_R_factor_R_work
                ls_R_factor_R_free
            }}
        }}
    }}
    """
    
    return graphql_query(query, timeout=timeout, max_retries=max_retries)

# ===== UTILITY FUNCTIONS =====

def get_all_current_pdb_ids(timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[List[str]]:
    """
    Get list of all current PDB IDs
    
    Args:
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    
    Returns:
        List of all current PDB identifiers
    """
    result = _make_request_data(HOLDINGS_URL, timeout=timeout, max_retries=max_retries)
    return result if result else None
