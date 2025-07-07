import time
import json
import requests
from typing import Dict, List, Optional, Literal, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

# chembl api module
from chembl_webresource_client.new_client import new_client

from agents.ligand_search.models import (
    LigandSearchResponse,
    SearchLigandsToolResult,
    LigandInfo,
    ToolsToUseResult
)

# =============================================================================
# CONFIGURATION & UTILITIES
# =============================================================================

# Common chemical database APIs
CHEMBL_BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3


def _make_request(
    url: str,
    params: Optional[Dict] = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Optional[Dict]:
    """Make HTTP request with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=timeout,
                headers={"Accept": "application/json"},
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"result_set": [], "total_count": 0}
            else:
                print(f"HTTP {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)

    return None


def _post_request(
    url: str,
    data: Optional[Dict] = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Optional[Dict]:
    """Make POST request with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                json=data,
                timeout=timeout,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"result_set": [], "total_count": 0}
            else:
                print(f"HTTP {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)

    return None

# =============================================================================
# CORE LIGAND SEARCH FUNCTIONS
# =============================================================================

## Inherited Fields from BaseLigandSearchResult
# tool_name: str
# success: bool = True
# execution_time: float = 0.0
# timestamp: datetime = Field(default_factory=datetime.now)
# query_params: Dict[str, Any] = {}
# error_message: str = ""
# warnings: List[str] = []
# ligands: List[LigandInfo] = []
# total_count: int = 0
# search_metadata: Dict[str, Any] = {}


## SearchLigandsToolResult
# tool_name: str = "search_ligands_tool"
# search_query: str = ""
# search_type: str = "name"  # name, smiles, inchi, formula
# exact_match: bool = False


## LigandInfo
# name: Optional[str] = None
# smiles: Optional[str] = None
# inchi: Optional[str] = None
# chembl_id: Optional[str] = None
# structure: Optional[str] = None  # MOL file contents
# properties: Dict[str, Any] = {}


def search_ligands(
    query: str,
    search_type: Literal["name", "smiles", "inchi", "formula", "chembl_id"] = "name",
    exact_match: bool = False
) -> Dict:
    """
    Comprehensive ligand search supporting multiple identifier types and matching strategies.
    
    This function provides the primary entry point for ligand discovery, supporting searches
    by compound name, chemical structure representations (SMILES, InChI), and molecular
    formula. It offers both exact and fuzzy matching to accommodate different use cases
    from precise identifier lookup to exploratory compound discovery.
    
    The function integrates with ChEMBL to provide comprehensive coverage of chemical space. 
    Results are ranked by relevance and include detailed metadata for downstream analysis.
    
    Args:
        query (str): Search term - can be compound name, SMILES string, InChI, 
                    molecular formula, or ChEMBL ID depending on search_type
        search_type (Literal): Type of search to perform:
                              - "name": Search by compound/drug name (default)
                              - "smiles": Search by SMILES chemical structure
                              - "inchi": Search by InChI identifier  
                              - "formula": Search by molecular formula
                              - "chembl_id": Search by ChEMBL identifier (e.g., CHEMBL25)        
    Returns:
        Dict: Comprehensive search results containing:
            - ligands (List[LigandInfo]): List of ligand information objects for found compounds
            - total_count (int): Total matches found (may exceed returned count)
            - execution_time (float): Time taken for search in seconds
            - search_metadata (Dict): Search parameters and context information
            - error_message (str): Error description if search failed (empty on success)
            
    Examples:
        >>> # Search for caffeine by name
        >>> result = search_ligands("caffeine", search_type="name")
        >>> print(f"Found {result['total_count']} caffeine-related compounds")

        >>> # Exact SMILES structure search
        >>> result = search_ligands("CCO", search_type="smiles")
        >>> print(f"Ethanol variants: {result['ligands']}")
        
        >>> # Molecular formula search with fuzzy matching
        >>> result = search_ligands("C8H10N4O2", search_type="formula")
        
        >>> # ChEMBL ID search
        >>> result = search_ligands("CHEMBL25", search_type="chembl_id")
        >>> print(f"Found compound: {result['ligands']}")
        
    Notes:
        - Name searches support both common names and IUPAC nomenclature
        - SMILES searches require valid chemical structure notation
        - ChEMBL ID searches work with standard ChEMBL identifiers (e.g., CHEMBL25)
    """
    start_time = time.time()

    try:
        results = []
        molecule_client = new_client.molecule

        if search_type == "name":
            # Search ChEMBL by compound name
            if exact_match:
                # Exact match search
                search_results = molecule_client.filter(pref_name__iexact=query)
            else:
                # Fuzzy match search
                search_results = molecule_client.filter(pref_name__icontains=query)

            results.extend(search_results)

        elif search_type == "smiles":
            # Search by SMILES structure
            if exact_match:
                # Exact match search
                search_results = molecule_client.filter(molecule_structures__canonical_smiles__iexact=query)
            else:
                # Fuzzy match search
                search_results = molecule_client.filter(molecule_structures__canonical_smiles__icontains=query)

            results.extend(search_results)

        elif search_type == "inchi":
            # Search by InChI identifier
            if exact_match:
                # Exact match search
                search_results = molecule_client.filter(molecule_structures__standard_inchi__iexact=query)
            else:
                # Fuzzy match search
                search_results = molecule_client.filter(molecule_structures__standard_inchi__icontains=query)

            results.extend(search_results)

        elif search_type == "formula":
            # Search by molecular formula
            if exact_match:
                # Exact match search
                search_results = molecule_client.filter(molecule_properties__full_molformula__iexact=query)
            else:
                # Fuzzy match search
                search_results = molecule_client.filter(molecule_properties__full_molformula__icontains=query)

            results.extend(search_results)

        elif search_type == "chembl_id":
            # Search by ChEMBL ID
            if exact_match:
                # Exact match search
                search_results = molecule_client.filter(molecule_chembl_id__iexact=query)
            else:
                # Fuzzy match search (useful for partial IDs like "CHEMBL25")
                search_results = molecule_client.filter(molecule_chembl_id__icontains=query)

            results.extend(search_results)
            
        execution_time = time.time() - start_time

        return { 
            "success": True,
            "ligands": results,
            "total_count": len(results),
            "execution_time": execution_time,
            "metadata": {
                "query": query,
                "search_type": search_type,
                "exact_match": exact_match
            },
            "error_message": None
        }

    except Exception as e:
        return { 
            "success": False,
            "ligands": [],
            "total_count": 0,
            "execution_time": time.time() - start_time,
            "metadata": {
                "query": query,
                "search_type": search_type,
                "exact_match": exact_match
            },
            "error_message": str(e)
        }
        
        