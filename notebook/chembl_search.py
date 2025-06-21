"""
ChEMBL Search API Wrapper for Drug Discovery and Lead Optimization

This module provides simplified access to ChEMBL database for common drug discovery tasks
including molecule search, similarity search, activity data retrieval, and target analysis.
"""

import time
import json
from typing import Dict, List, Optional, Union, Literal
from chembl_webresource_client.new_client import new_client

# Default configuration
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_SIMILARITY_THRESHOLD = 70
DEFAULT_ACTIVITY_LIMIT = 1000

def _safe_request(client_method, max_retries: int = DEFAULT_MAX_RETRIES, **kwargs):
    """
    Safely execute ChEMBL client requests with retries and error handling.
    """
    for attempt in range(max_retries):
        try:
            result = client_method(**kwargs)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Error after {max_retries} attempts: {str(e)}")
                return None
            time.sleep(1)  # Wait before retry
    return None

def _parse_molecule_results(molecules, limit: Optional[int] = None) -> Dict:
    """Parse and format molecule search results."""
    if not molecules:
        return {"count": 0, "results": []}
    
    results = []
    count = 0
    
    for mol in molecules:
        if limit and count >= limit:
            break
        
        result = {
            "chembl_id": mol.get("molecule_chembl_id"),
            "pref_name": mol.get("pref_name"),
            "smiles": mol.get("molecule_structures", {}).get("canonical_smiles") if mol.get("molecule_structures") else None,
            "inchi_key": mol.get("molecule_structures", {}).get("standard_inchi_key") if mol.get("molecule_structures") else None,
            "molecular_weight": mol.get("molecule_properties", {}).get("full_mwt") if mol.get("molecule_properties") else None,
            "alogp": mol.get("molecule_properties", {}).get("alogp") if mol.get("molecule_properties") else None,
            "max_phase": mol.get("max_phase"),
            "indication_class": mol.get("indication_class")
        }
        results.append(result)
        count += 1
    
    return {"count": count, "results": results}

def molecule_search(identifier: str, identifier_type: Literal["chembl_id", "name", "smiles", "inchi_key"] = "name", 
                   limit: int = 100, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for molecules by various identifiers.
    
    Args:
        identifier: The identifier to search for
        identifier_type: Type of identifier ('chembl_id', 'name', 'smiles', 'inchi_key')
        limit: Maximum number of results to return
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary containing search results
    """
    molecule = new_client.molecule
    
    try:
        if identifier_type == "chembl_id":
            results = _safe_request(
                molecule.filter,
                molecule_chembl_id=identifier,
                max_retries=max_retries
            )
        elif identifier_type == "name":
            results = _safe_request(
                molecule.filter,
                pref_name__icontains=identifier,
                max_retries=max_retries
            )
        elif identifier_type == "smiles":
            results = _safe_request(
                molecule.filter,
                molecule_structures__canonical_smiles__exact=identifier,
                max_retries=max_retries
            )
        elif identifier_type == "inchi_key":
            results = _safe_request(
                molecule.filter,
                molecule_structures__standard_inchi_key=identifier,
                max_retries=max_retries
            )
        else:
            return {"error": f"Invalid identifier_type: {identifier_type}"}
        
        return _parse_molecule_results(results, limit)
        
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

def similarity_search(query_smiles: str, similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
                     limit: int = 100, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Find molecules similar to a query SMILES string.
    
    Args:
        query_smiles: SMILES string to search for similar molecules
        similarity_threshold: Minimum similarity score (0-100)
        limit: Maximum number of results to return
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary containing similar molecules with similarity scores
    """
    similarity = new_client.similarity
    
    try:
        results = _safe_request(
            similarity.filter,
            smiles=query_smiles,
            similarity=similarity_threshold,
            max_retries=max_retries
        )
        
        if not results:
            return {"count": 0, "results": []}
        
        # Get detailed molecule information
        molecule_ids = [r['molecule_chembl_id'] for r in results[:limit]]
        molecule = new_client.molecule
        molecules = _safe_request(
            molecule.filter,
            molecule_chembl_id__in=molecule_ids,
            max_retries=max_retries
        )
        
        # Combine similarity scores with molecule data
        similarity_map = {r['molecule_chembl_id']: r['similarity'] for r in results}
        
        formatted_results = []
        for mol in molecules:
            chembl_id = mol.get("molecule_chembl_id")
            result = {
                "chembl_id": chembl_id,
                "similarity_score": similarity_map.get(chembl_id),
                "pref_name": mol.get("pref_name"),
                "smiles": mol.get("molecule_structures", {}).get("canonical_smiles") if mol.get("molecule_structures") else None,
                "molecular_weight": mol.get("molecule_properties", {}).get("full_mwt") if mol.get("molecule_properties") else None,
                "max_phase": mol.get("max_phase")
            }
            formatted_results.append(result)
        
        return {"count": len(formatted_results), "results": formatted_results}
        
    except Exception as e:
        return {"error": f"Similarity search failed: {str(e)}"}

def substructure_search(query_smiles: str, limit: int = 100, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for molecules containing a specific substructure.
    
    Args:
        query_smiles: SMILES string representing the substructure
        limit: Maximum number of results to return
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary containing molecules with the substructure
    """
    substructure = new_client.substructure
    
    try:
        results = _safe_request(
            substructure.filter,
            smiles=query_smiles,
            max_retries=max_retries
        )
        
        if not results:
            return {"count": 0, "results": []}
        
        # Get detailed molecule information
        molecule_ids = [r['molecule_chembl_id'] for r in results[:limit]]
        molecule = new_client.molecule
        molecules = _safe_request(
            molecule.filter,
            molecule_chembl_id__in=molecule_ids,
            max_retries=max_retries
        )
        
        return _parse_molecule_results(molecules, limit)
        
    except Exception as e:
        return {"error": f"Substructure search failed: {str(e)}"}

def activity_search(molecule_chembl_id: str = None, target_chembl_id: str = None, 
                   activity_types: List[str] = None, limit: int = DEFAULT_ACTIVITY_LIMIT,
                   max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for bioactivity data for molecules and/or targets.
    
    Args:
        molecule_chembl_id: ChEMBL ID of the molecule
        target_chembl_id: ChEMBL ID of the target
        activity_types: List of activity types (e.g., ['IC50', 'Ki', 'EC50'])
        limit: Maximum number of results to return
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary containing activity data
    """
    activity = new_client.activity
    
    try:
        filters = {}
        if molecule_chembl_id:
            filters['molecule_chembl_id'] = molecule_chembl_id
        if target_chembl_id:
            filters['target_chembl_id'] = target_chembl_id
        if activity_types:
            filters['standard_type__in'] = activity_types
        
        if not filters:
            return {"error": "At least one filter parameter must be provided"}
        
        results = _safe_request(activity.filter, max_retries=max_retries, **filters)
        
        if not results:
            return {"count": 0, "results": []}
        
        formatted_results = []
        count = 0
        
        for act in results:
            if limit and count >= limit:
                break
            
            result = {
                "molecule_chembl_id": act.get("molecule_chembl_id"),
                "target_chembl_id": act.get("target_chembl_id"),
                "activity_type": act.get("standard_type"),
                "activity_value": act.get("standard_value"),
                "activity_units": act.get("standard_units"),
                "pchembl_value": act.get("pchembl_value"),
                "assay_chembl_id": act.get("assay_chembl_id"),
                "assay_type": act.get("assay_type"),
                "confidence_score": act.get("confidence_score")
            }
            formatted_results.append(result)
            count += 1
        
        return {"count": count, "results": formatted_results}
        
    except Exception as e:
        return {"error": f"Activity search failed: {str(e)}"}

def target_search(query: str, search_type: Literal["name", "gene_name", "chembl_id"] = "name",
                 limit: int = 100, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for targets by name, gene name, or ChEMBL ID.
    
    Args:
        query: Search query string
        search_type: Type of search ('name', 'gene_name', 'chembl_id')
        limit: Maximum number of results to return
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary containing target information
    """
    target = new_client.target
    
    try:
        if search_type == "name":
            results = _safe_request(
                target.filter,
                pref_name__icontains=query,
                max_retries=max_retries
            )
        elif search_type == "gene_name":
            results = _safe_request(
                target.filter,
                target_synonym__icontains=query,
                max_retries=max_retries
            )
        elif search_type == "chembl_id":
            results = _safe_request(
                target.filter,
                target_chembl_id=query,
                max_retries=max_retries
            )
        else:
            return {"error": f"Invalid search_type: {search_type}"}
        
        if not results:
            return {"count": 0, "results": []}
        
        formatted_results = []
        count = 0
        
        for tgt in results:
            if limit and count >= limit:
                break
            
            result = {
                "target_chembl_id": tgt.get("target_chembl_id"),
                "pref_name": tgt.get("pref_name"),
                "target_type": tgt.get("target_type"),
                "organism": tgt.get("organism"),
                "species_group_flag": tgt.get("species_group_flag")
            }
            formatted_results.append(result)
            count += 1
        
        return {"count": count, "results": formatted_results}
        
    except Exception as e:
        return {"error": f"Target search failed: {str(e)}"}

def drug_search(max_phase: int = 4, indication_class: str = None, 
               molecular_weight_max: float = None, alogp_max: float = None,
               limit: int = 100, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for approved drugs and drug candidates with optional filters.
    
    Args:
        max_phase: Maximum development phase (1-4, where 4 is approved)
        indication_class: Therapeutic indication class
        molecular_weight_max: Maximum molecular weight
        alogp_max: Maximum ALogP value
        limit: Maximum number of results to return
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary containing drug information
    """
    molecule = new_client.molecule
    
    try:
        filters = {"max_phase__gte": max_phase}
        
        if indication_class:
            filters["indication_class__icontains"] = indication_class
        if molecular_weight_max:
            filters["molecule_properties__full_mwt__lte"] = molecular_weight_max
        if alogp_max:
            filters["molecule_properties__alogp__lte"] = alogp_max
        
        results = _safe_request(molecule.filter, max_retries=max_retries, **filters)
        
        return _parse_molecule_results(results, limit)
        
    except Exception as e:
        return {"error": f"Drug search failed: {str(e)}"}

def drug_like_molecules(ro5_violations: int = 0, qed_min: float = 0.5,
                       limit: int = 100, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for drug-like molecules based on Lipinski's Rule of Five and QED.
    
    Args:
        ro5_violations: Maximum number of Rule of Five violations (0-4)
        qed_min: Minimum QED (Quantitative Estimate of Drug-likeness) score
        limit: Maximum number of results to return
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary containing drug-like molecules
    """
    molecule = new_client.molecule
    
    try:
        filters = {
            "molecule_properties__num_ro5_violations__lte": ro5_violations,
            "molecule_properties__qed_weighted__gte": qed_min
        }
        
        results = _safe_request(molecule.filter, max_retries=max_retries, **filters)
        
        return _parse_molecule_results(results, limit)
        
    except Exception as e:
        return {"error": f"Drug-like molecule search failed: {str(e)}"}

def get_molecule_properties(chembl_id: str, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Get detailed molecular properties for a specific ChEMBL molecule.
    
    Args:
        chembl_id: ChEMBL ID of the molecule
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary containing molecular properties
    """
    molecule = new_client.molecule
    
    try:
        results = _safe_request(
            molecule.filter,
            molecule_chembl_id=chembl_id,
            max_retries=max_retries
        )
        
        if not results:
            return {"error": f"Molecule {chembl_id} not found"}
        
        mol = results[0]
        properties = mol.get("molecule_properties", {})
        structures = mol.get("molecule_structures", {})
        
        return {
            "chembl_id": mol.get("molecule_chembl_id"),
            "pref_name": mol.get("pref_name"),
            "smiles": structures.get("canonical_smiles"),
            "inchi": structures.get("standard_inchi"),
            "inchi_key": structures.get("standard_inchi_key"),
            "molecular_weight": properties.get("full_mwt"),
            "alogp": properties.get("alogp"),
            "hbd": properties.get("hbd"),
            "hba": properties.get("hba"),
            "psa": properties.get("psa"),
            "rotatable_bonds": properties.get("rtb"),
            "aromatic_rings": properties.get("aromatic_rings"),
            "qed_weighted": properties.get("qed_weighted"),
            "ro5_violations": properties.get("num_ro5_violations"),
            "max_phase": mol.get("max_phase"),
            "therapeutic_flag": mol.get("therapeutic_flag"),
            "indication_class": mol.get("indication_class")
        }
        
    except Exception as e:
        return {"error": f"Failed to get molecule properties: {str(e)}"}

def get_target_activities(target_chembl_id: str, activity_types: List[str] = None,
                         limit: int = DEFAULT_ACTIVITY_LIMIT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Get all activities for a specific target.
    
    Args:
        target_chembl_id: ChEMBL ID of the target
        activity_types: List of activity types to filter (e.g., ['IC50', 'Ki'])
        limit: Maximum number of results to return
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary containing target activities
    """
    return activity_search(
        target_chembl_id=target_chembl_id,
        activity_types=activity_types,
        limit=limit,
        max_retries=max_retries
    )

def get_chembl_stats(max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Get general statistics about the ChEMBL database.
    
    Args:
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dictionary containing database statistics
    """
    try:
        molecule = new_client.molecule
        target = new_client.target
        activity = new_client.activity
        
        stats = {
            "total_compounds": len(_safe_request(molecule.all, max_retries=max_retries) or []),
            "approved_drugs": len(_safe_request(molecule.filter, max_phase=4, max_retries=max_retries) or []),
            "total_targets": len(_safe_request(target.all, max_retries=max_retries) or []),
            "total_activities": len(_safe_request(activity.all, max_retries=max_retries) or [])
        }
        
        return stats
        
    except Exception as e:
        return {"error": f"Failed to get ChEMBL stats: {str(e)}"} 