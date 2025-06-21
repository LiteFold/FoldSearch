import requests
from typing import Dict, List, Optional, Literal, Union
import time
import json


BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3

def _make_request(url: str, method: str = "GET", data: Dict = None, timeout: int = DEFAULT_TIMEOUT, 
                 max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Union[Dict, List, str]]:
    """Make HTTP request with retry logic"""
    for attempt in range(max_retries):
        try:
            if method.upper() == "POST":
                response = requests.post(
                    url,
                    data=data,
                    timeout=timeout,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
            else:
                response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                # Handle different content types
                content_type = response.headers.get('content-type', '').lower()
                if 'application/json' in content_type:
                    return response.json()
                elif 'text/plain' in content_type:
                    # For TXT responses, split lines and filter empty
                    return [line.strip() for line in response.text.strip().split('\n') if line.strip()]
                elif 'text/csv' in content_type:
                    return response.text
                else:
                    return response.text
                    
            elif response.status_code == 404:
                return {"error": "No results found", "status_code": 404}
            elif response.status_code == 503:
                print(f"Server busy (503), retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)
                continue
            else:
                print(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                
    return None

def _parse_compound_results(response: Union[Dict, List, str], limit: Optional[int] = None) -> Dict:
    """Parse API response to extract compound information"""
    if not response or (isinstance(response, dict) and "error" in response):
        return {"cids": [], "total_count": 0, "data": {}}
    
    cids = []
    data = {}
    
    if isinstance(response, list):
        # TXT response with list of CIDs
        cids = [str(cid) for cid in response if str(cid).isdigit()]
    elif isinstance(response, dict):
        # JSON response
        if "IdentifierList" in response:
            cids = [str(cid) for cid in response["IdentifierList"].get("CID", [])]
        elif "PropertyTable" in response:
            props = response["PropertyTable"]["Properties"]
            cids = [str(prop["CID"]) for prop in props]
            data = {str(prop["CID"]): prop for prop in props}
        elif "InformationList" in response:
            info_list = response["InformationList"]["Information"]
            for info in info_list:
                cid = str(info.get("CID", ""))
                if cid:
                    cids.append(cid)
                    data[cid] = info
    
    # Apply limit if specified
    if limit and len(cids) > limit:
        cids = cids[:limit]
        if data:
            data = {k: v for k, v in data.items() if k in cids}
    
    return {
        "cids": cids,
        "total_count": len(cids),
        "data": data,
        "returned_count": len(cids)
    }

# ===== BASIC SEARCH FUNCTIONS =====

def compound_by_name(name: str, name_type: Literal["complete", "word"] = "complete", 
                    limit: int = 100, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search compounds by chemical name
    
    Args:
        name: Chemical name (e.g., "aspirin", "glucose")
        name_type: "complete" for exact match, "word" for word match
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with cids, total_count, data, returned_count
    """
    url = f"{BASE_URL}/compound/name/{name}/cids/JSON"
    if name_type == "word":
        url += "?name_type=word"
    
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    return _parse_compound_results(response, limit)

def compound_by_smiles(smiles: str, limit: int = 100, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search compounds by SMILES string
    
    Args:
        smiles: SMILES string (e.g., "CC(=O)OC1=CC=CC=C1C(=O)O" for aspirin)
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with cids, total_count, data, returned_count
    """
    url = f"{BASE_URL}/compound/smiles/{smiles}/cids/JSON"
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    return _parse_compound_results(response, limit)

def compound_by_inchi_key(inchi_key: str, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search compounds by InChI Key
    
    Args:
        inchi_key: InChI Key (e.g., "BSYNRYMUTXBXSQ-UHFFFAOYSA-N" for aspirin)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with cids, total_count, data, returned_count
    """
    url = f"{BASE_URL}/compound/inchikey/{inchi_key}/cids/JSON"
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    return _parse_compound_results(response)

def compound_by_formula(formula: str, allow_other_elements: bool = False, limit: int = 100,
                       timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search compounds by molecular formula
    
    Args:
        formula: Molecular formula (e.g., "C9H8O4")
        allow_other_elements: Allow additional elements beyond specified
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with cids, total_count, data, returned_count
    """
    url = f"{BASE_URL}/compound/fastformula/{formula}/cids/JSON?MaxRecords={min(limit, 10000)}"
    if allow_other_elements:
        url += "&AllowOtherElements=true"
    
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    return _parse_compound_results(response, limit)

# ===== PROPERTY RETRIEVAL =====

def get_compound_properties(cids: Union[str, int, List[Union[str, int]]], 
                          properties: List[str] = None, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Get properties for compounds
    
    Args:
        cids: Single CID or list of CIDs
        properties: List of properties to retrieve (default: common properties)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with cids, total_count, data (properties), returned_count
    """
    if properties is None:
        properties = [
            "MolecularFormula", "MolecularWeight", "SMILES", "InChI", "InChIKey",
            "IUPACName", "XLogP", "ExactMass", "TPSA", "Complexity", "Charge",
            "HBondDonorCount", "HBondAcceptorCount", "RotatableBondCount"
        ]
    
    if isinstance(cids, (str, int)):
        cids = [str(cids)]
    else:
        cids = [str(cid) for cid in cids]
    
    cid_string = ",".join(cids)
    prop_string = ",".join(properties)
    
    url = f"{BASE_URL}/compound/cid/{cid_string}/property/{prop_string}/JSON"
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    return _parse_compound_results(response)

def get_compound_synonyms(cid: Union[str, int], timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Get synonyms for a compound
    
    Args:
        cid: Compound CID
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with synonyms list
    """
    url = f"{BASE_URL}/compound/cid/{cid}/synonyms/JSON"
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    
    if response and "InformationList" in response:
        info = response["InformationList"]["Information"][0]
        return {
            "cid": str(info.get("CID", "")),
            "synonyms": info.get("Synonym", []),
            "total_synonyms": len(info.get("Synonym", []))
        }
    
    return {"cid": str(cid), "synonyms": [], "total_synonyms": 0}

# ===== STRUCTURE SEARCHES =====

def substructure_search(query: str, query_type: Literal["smiles", "cid"] = "smiles", 
                       strip_hydrogen: bool = True, max_records: int = 1000,
                       timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for compounds containing a substructure
    
    Args:
        query: SMILES string or CID for substructure search
        query_type: Type of query ("smiles" or "cid")
        strip_hydrogen: Remove explicit hydrogens before searching
        max_records: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with cids, total_count, data, returned_count
    """
    url = f"{BASE_URL}/compound/fastsubstructure/{query_type}/{query}/cids/JSON"
    url += f"?MaxRecords={min(max_records, 10000)}"
    if strip_hydrogen:
        url += "&StripHydrogen=true"
    
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    return _parse_compound_results(response)

def similarity_search(query: str, query_type: Literal["smiles", "cid"] = "smiles",
                     threshold: int = 90, max_records: int = 1000,
                     timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for compounds with similar 2D structure (Tanimoto similarity)
    
    Args:
        query: SMILES string or CID for similarity search
        query_type: Type of query ("smiles" or "cid")
        threshold: Minimum Tanimoto similarity score (0-100)
        max_records: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with cids, total_count, data, returned_count
    """
    url = f"{BASE_URL}/compound/fastsimilarity_2d/{query_type}/{query}/cids/JSON"
    url += f"?Threshold={threshold}&MaxRecords={min(max_records, 10000)}"
    
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    return _parse_compound_results(response)

def identity_search(query: str, query_type: Literal["smiles", "cid"] = "smiles",
                   identity_type: str = "same_connectivity", max_records: int = 1000,
                   timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for compounds with identical or related structures
    
    Args:
        query: SMILES string or CID for identity search
        query_type: Type of query ("smiles" or "cid")  
        identity_type: Type of identity match
        max_records: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with cids, total_count, data, returned_count
    """
    url = f"{BASE_URL}/compound/fastidentity/{query_type}/{query}/cids/JSON"
    url += f"?identity_type={identity_type}&MaxRecords={min(max_records, 10000)}"
    
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    return _parse_compound_results(response)

# ===== MASS-BASED SEARCHES =====

def search_by_mass(mass: float, mass_type: Literal["molecular_weight", "exact_mass", "monoisotopic_mass"] = "molecular_weight",
                  tolerance: float = 0.1, limit: int = 100, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search compounds by mass within tolerance
    
    Args:
        mass: Target mass value
        mass_type: Type of mass to search
        tolerance: Mass tolerance (+/- daltons)
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with cids, total_count, data, returned_count
    """
    min_mass = mass - tolerance
    max_mass = mass + tolerance
    
    url = f"{BASE_URL}/compound/{mass_type}/range/{min_mass}/{max_mass}/cids/JSON"
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    return _parse_compound_results(response, limit)

# ===== BIOASSAY SEARCHES =====

def get_bioassay_data(aid: Union[str, int], timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Get bioassay description and summary
    
    Args:
        aid: Assay AID
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with assay information
    """
    # Get assay description
    desc_url = f"{BASE_URL}/assay/aid/{aid}/description/JSON"
    desc_response = _make_request(desc_url, timeout=timeout, max_retries=max_retries)
    
    # Get assay summary
    summary_url = f"{BASE_URL}/assay/aid/{aid}/summary/JSON"
    summary_response = _make_request(summary_url, timeout=timeout, max_retries=max_retries)
    
    return {
        "aid": str(aid),
        "description": desc_response,
        "summary": summary_response
    }

def search_assays_by_target(target: str, target_type: Literal["genesymbol", "geneid", "gi"] = "genesymbol",
                           limit: int = 100, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search bioassays by target protein/gene
    
    Args:
        target: Target identifier (gene symbol, gene ID, or GI)
        target_type: Type of target identifier
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with AIDs
    """
    url = f"{BASE_URL}/assay/target/{target_type}/{target}/aids/JSON"
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    
    aids = []
    if response and "IdentifierList" in response:
        aids = [str(aid) for aid in response["IdentifierList"].get("AID", [])]
    
    # Apply limit
    if limit and len(aids) > limit:
        aids = aids[:limit]
    
    return {
        "aids": aids,
        "total_count": len(aids),
        "target": target,
        "target_type": target_type
    }

def get_compound_bioactivity(cid: Union[str, int], timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Get bioactivity summary for a compound
    
    Args:
        cid: Compound CID
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with bioactivity data
    """
    url = f"{BASE_URL}/compound/cid/{cid}/assaysummary/JSON"
    response = _make_request(url, timeout=timeout, max_retries=max_retries)
    
    activities = []
    if response and "Table" in response:
        activities = response["Table"]["Row"]
    
    return {
        "cid": str(cid),
        "bioactivities": activities,
        "total_activities": len(activities)
    }

# ===== ADVANCED SEARCHES =====

def drug_like_compounds(limit: int = 100, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for drug-like compounds using Lipinski's Rule of Five criteria
    
    Args:
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with drug-like compounds
    """
    # Search for compounds in a reasonable molecular weight range
    results = search_by_mass(300, mass_type="molecular_weight", tolerance=200, limit=limit*2, 
                           timeout=timeout, max_retries=max_retries)
    
    if results["cids"]:
        # Get properties to filter by drug-like criteria
        props_results = get_compound_properties(
            results["cids"][:limit], 
            properties=["MolecularWeight", "XLogP", "HBondDonorCount", "HBondAcceptorCount"],
            timeout=timeout, max_retries=max_retries
        )
        
        # Filter by Lipinski's Rule of Five
        drug_like_cids = []
        for cid, props in props_results["data"].items():
            mw = props.get("MolecularWeight", 1000)
            logp = props.get("XLogP", 10)
            hbd = props.get("HBondDonorCount", 10)
            hba = props.get("HBondAcceptorCount", 20)
            
            if (mw <= 500 and logp <= 5 and hbd <= 5 and hba <= 10):
                drug_like_cids.append(cid)
                if len(drug_like_cids) >= limit:
                    break
        
        return {
            "cids": drug_like_cids,
            "total_count": len(drug_like_cids),
            "data": {cid: props_results["data"][cid] for cid in drug_like_cids},
            "criteria": "Lipinski's Rule of Five"
        }
    
    return {"cids": [], "total_count": 0, "data": {}}

def complex_search(name_query: str = None, formula: str = None, mass_range: tuple = None,
                  similarity_query: str = None, similarity_threshold: int = 90,
                  limit: int = 100, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Combined search with multiple criteria
    
    Args:
        name_query: Chemical name to search
        formula: Molecular formula
        mass_range: Tuple of (min_mass, max_mass)
        similarity_query: SMILES for similarity search
        similarity_threshold: Similarity threshold (0-100)
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with combined search results
    """
    all_cids = set()
    search_results = {}
    
    # Name search
    if name_query:
        name_results = compound_by_name(name_query, limit=limit*2, timeout=timeout, max_retries=max_retries)
        all_cids.update(name_results["cids"])
        search_results["name_search"] = name_results
    
    # Formula search
    if formula:
        formula_results = compound_by_formula(formula, limit=limit*2, timeout=timeout, max_retries=max_retries)
        if all_cids:
            all_cids.intersection_update(formula_results["cids"])
        else:
            all_cids.update(formula_results["cids"])
        search_results["formula_search"] = formula_results
    
    # Mass search
    if mass_range:
        min_mass, max_mass = mass_range
        mass_results = search_by_mass((min_mass + max_mass) / 2, tolerance=(max_mass - min_mass) / 2,
                                    limit=limit*2, timeout=timeout, max_retries=max_retries)
        if all_cids:
            all_cids.intersection_update(mass_results["cids"])
        else:
            all_cids.update(mass_results["cids"])
        search_results["mass_search"] = mass_results
    
    # Similarity search
    if similarity_query:
        sim_results = similarity_search(similarity_query, threshold=similarity_threshold,
                                      max_records=limit*2, timeout=timeout, max_retries=max_retries)
        if all_cids:
            all_cids.intersection_update(sim_results["cids"])
        else:
            all_cids.update(sim_results["cids"])
        search_results["similarity_search"] = sim_results
    
    final_cids = list(all_cids)[:limit]
    
    return {
        "cids": final_cids,
        "total_count": len(final_cids),
        "individual_searches": search_results,
        "returned_count": len(final_cids)
    }

# ===== UTILITY FUNCTIONS =====

def get_compound_image(cid: Union[str, int], image_size: str = "large", 
                      timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> bytes:
    """
    Get compound structure image
    
    Args:
        cid: Compound CID
        image_size: Image size ("large", "small", or "WIDTHxHEIGHT")
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Image data as bytes
    """
    url = f"{BASE_URL}/compound/cid/{cid}/PNG?image_size={image_size}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.content
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    return b""

def get_pubchem_stats(timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Get basic PubChem database statistics
    
    Args:
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with database statistics
    """
    stats = {}
    
    # Try to get some basic counts through searches
    try:
        # Sample organic compounds
        organic_results = compound_by_formula("C", limit=1, timeout=timeout, max_retries=max_retries)
        stats["has_carbon_compounds"] = "Available"
        
        # Sample with common elements
        common_results = compound_by_formula("H", limit=1, timeout=timeout, max_retries=max_retries) 
        stats["has_hydrogen_compounds"] = "Available"
        
        stats["database_status"] = "Active"
        stats["note"] = "PubChem contains millions of compounds - exact counts require specialized queries"
        
    except Exception as e:
        stats["error"] = str(e)
        stats["database_status"] = "Unknown"
    
    return stats

def validate_smiles(smiles: str, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Validate and standardize a SMILES string
    
    Args:
        smiles: SMILES string to validate
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with validation results
    """
    url = f"{BASE_URL}/standardize/smiles/{smiles}/SDF"
    response = _make_request(url, method="POST", data={"smiles": smiles}, timeout=timeout, max_retries=max_retries)
    
    if response and not isinstance(response, dict):
        return {
            "valid": True,
            "standardized_sdf": response,
            "original_smiles": smiles
        }
    else:
        return {
            "valid": False,
            "error": "Invalid SMILES string",
            "original_smiles": smiles
        } 