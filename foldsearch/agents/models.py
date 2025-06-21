from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

# ===== WEB RESEARCH MODELS =====

class SearchResult(BaseModel):
    title: str
    url: str
    abstract: str

class WebResearchResult(BaseModel):
    search_result: list[SearchResult]

class UpNextQueries(BaseModel):
    queries: list[str]

class WebResearchAgentModel(BaseModel):
    query: str
    raw_result: str
    research_paper: WebResearchResult
    upnext_queries: list[str]

# ===== PROTEIN SEARCH MODELS =====

class ToolsToUseResult(BaseModel):
    tools_to_use: list[str]

class ProteinSearchUnifiedResults(BaseModel):
    """
    Single comprehensive DTO for ALL protein search agent responses.
    Contains every possible field from all 10 functions in tooling.py.
    Most fields will be None for any given operation.
    """
    
    # ===== OPERATION METADATA =====
    operation_type: Optional[str] = None
    tool_used: Optional[str] = None
    query_params: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    
    # ===== BASIC SEARCH RESULTS (search_structures, search_by_sequence, search_by_chemical, get_high_quality_structures) =====
    pdb_ids: Optional[List[str]] = None
    total_count: Optional[int] = None
    returned_count: Optional[int] = None
    scores: Optional[Dict[str, float]] = None
    
    # ===== STRUCTURE SEARCH SPECIFIC (search_by_structure) =====
    by_reference: Optional[Dict[str, Any]] = None
    
    # ===== DETAILED STRUCTURE INFORMATION (get_structure_details, get_structural_summary) =====
    structure_details: Optional[Dict[str, Any]] = None
    
    # Flattened structure detail fields for individual structures
    pdb_id: Optional[str] = None
    title: Optional[str] = None
    method: Optional[str] = None
    resolution_A: Optional[float] = None
    r_work: Optional[float] = None
    r_free: Optional[float] = None
    space_group: Optional[str] = None
    polymer_entity_count: Optional[int] = None
    ligands: Optional[List[str]] = None
    deposition_date: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    assembly: Optional[Dict[str, Any]] = None
    
    # Assembly specific fields
    oligomeric_state: Optional[str] = None
    oligomeric_count: Optional[int] = None
    assembly_method: Optional[str] = None
    
    # Quality metrics
    quality_score: Optional[str] = None
    
    # Composition information (get_structural_summary)
    protein_entities: Optional[int] = None
    total_entities: Optional[int] = None
    ligand_count: Optional[int] = None
    unique_organisms: Optional[int] = None
    organisms: Optional[List[str]] = None
    
    # Research relevance indicators
    has_ligands: Optional[bool] = None
    is_complex: Optional[bool] = None
    high_resolution: Optional[bool] = None
    
    # ===== SEQUENCE INFORMATION (get_sequences) =====
    sequences: Optional[Dict[str, Any]] = None
    
    # Flattened sequence fields for individual sequences
    entity_id: Optional[str] = None
    sequence: Optional[str] = None
    sequence_length: Optional[int] = None
    sequence_type: Optional[str] = None
    molecule_type: Optional[str] = None
    
    # ===== COMPARISON RESULTS (compare_structures) =====
    comparisons: Optional[Dict[str, Any]] = None
    comparison_summary: Optional[Dict[str, Any]] = None
    
    # Flattened comparison fields
    sequence_identity: Optional[float] = None
    length_difference: Optional[int] = None
    structural_similarity: Optional[float] = None
    comparison_note: Optional[str] = None
    
    # ===== INTERACTION ANALYSIS (analyze_interactions) =====
    interactions: Optional[Dict[str, Any]] = None
    
    # Flattened interaction fields
    protein_chains: Optional[List[str]] = None
    interaction_types: Optional[List[str]] = None
    interaction_descriptions: Optional[List[str]] = None
    quaternary_structure: Optional[Dict[str, Any]] = None
    
    # Protein-protein interaction fields
    multi_chain_complex: Optional[bool] = None
    chain_count: Optional[int] = None
    
    # Protein-ligand interaction fields
    protein_ligand_interactions: Optional[bool] = None
    bound_ligands: Optional[List[str]] = None
    
    # ===== EXPERIMENTAL INFORMATION =====
    experimental_method: Optional[str] = None
    experimental_details: Optional[Dict[str, Any]] = None
    
    # ===== ORGANISM INFORMATION =====
    organism: Optional[str] = None
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    taxonomy_id: Optional[int] = None
    
    # ===== CHEMICAL INFORMATION =====
    smiles: Optional[str] = None
    inchi: Optional[str] = None
    ligand_name: Optional[str] = None
    chemical_identifier: Optional[str] = None
    
    # ===== SEARCH PARAMETERS (tracking what was searched for) =====
    search_query: Optional[str] = None
    search_organism: Optional[str] = None
    search_method: Optional[str] = None
    max_resolution: Optional[float] = None
    identity_cutoff: Optional[float] = None
    evalue_cutoff: Optional[float] = None
    reference_pdb_ids: Optional[List[str]] = None
    assembly_id: Optional[str] = None
    match_type: Optional[str] = None
    
    # ===== QUALITY FILTERS =====
    max_r_work: Optional[float] = None
    max_r_free: Optional[float] = None
    min_year: Optional[int] = None
    
    # ===== PAGINATION/LIMITS =====
    limit: Optional[int] = None
    start_index: Optional[int] = None
    
    # ===== RAW DATA =====
    raw_response: Optional[Dict[str, Any]] = None
    raw_query: Optional[Dict[str, Any]] = None
    
    # ===== COUNTS AND STATISTICS =====
    total_structures: Optional[int] = None
    successful_retrievals: Optional[int] = None
    failed_retrievals: Optional[int] = None
    
    # ===== MULTIPLE STRUCTURE HANDLING =====
    multiple_structures: Optional[bool] = None
    structure_count: Optional[int] = None
    
    # ===== NOTES AND ADDITIONAL INFO =====
    notes: Optional[List[str]] = None
    additional_info: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        extra = "allow"  # Allow additional fields for future extensions
        
    def has_results(self) -> bool:
        """Check if there are any meaningful results"""
        return (
            (self.pdb_ids and len(self.pdb_ids) > 0) or
            (self.structure_details and len(self.structure_details) > 0) or
            (self.sequences and len(self.sequences) > 0) or
            (self.comparisons and len(self.comparisons) > 0) or
            (self.interactions and len(self.interactions) > 0) or
            bool(self.pdb_id)
        )
    
    def get_operation_summary(self) -> str:
        """Get a summary of what operation was performed and results"""
        op = self.operation_type or self.tool_used or "Unknown operation"
        count = self.get_result_count()
        
        if not self.success:
            return f"{op} failed: {self.error_message}"
        elif count == 0:
            return f"{op} completed with no results"
        else:
            return f"{op} completed with {count} results"
    
    def get_result_count(self) -> int:
        """Get the count of results from various possible result fields"""
        if self.pdb_ids:
            return len(self.pdb_ids)
        elif self.returned_count:
            return self.returned_count
        elif self.total_count:
            return self.total_count
        elif self.structure_count:
            return self.structure_count
        elif self.successful_retrievals:
            return self.successful_retrievals
        else:
            return 0

# ===== UNIFIED AGENT MODELS =====

class CombinedSearchResult(BaseModel):
    """
    Combined result model that can handle both web research and protein search results
    Uses Dict types to avoid cross-module validation issues
    """
    query: str
    
    # Web research results - using Dict to avoid validation issues
    web_research: Optional[Dict[str, Any]] = None
    
    # Protein search results - using Dict to avoid validation issues  
    protein_search: Optional[Dict[str, Any]] = None
    
    # Combined metadata
    search_type: str  # 'web', 'protein', or 'combined'
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None
    
    class Config:
        extra = "allow"
    
    def has_web_results(self) -> bool:
        """Check if there are web research results"""
        return (
            self.web_research is not None and 
            isinstance(self.web_research.get('research_paper'), dict) and
            isinstance(self.web_research['research_paper'].get('search_result'), list) and
            len(self.web_research['research_paper']['search_result']) > 0
        )
    
    def has_protein_results(self) -> bool:
        """Check if there are protein search results"""
        return (
            self.protein_search is not None and 
            (
                (isinstance(self.protein_search.get('pdb_ids'), list) and len(self.protein_search['pdb_ids']) > 0) or
                (isinstance(self.protein_search.get('total_count'), int) and self.protein_search['total_count'] > 0)
            )
        )
    
    def get_summary(self) -> str:
        """Get a summary of all results"""
        summaries = []
        
        if self.has_web_results():
            web_count = len(self.web_research['research_paper']['search_result'])
            summaries.append(f"{web_count} web results")
        
        if self.has_protein_results():
            pdb_count = self.protein_search.get('total_count', 0)
            operation = self.protein_search.get('operation_type', 'protein_search')
            summaries.append(f"Protein: {operation} completed with {pdb_count} results")
        
        if not summaries:
            return "No results found"
        
        return "; ".join(summaries)
