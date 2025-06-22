from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class ToolsToUseResult(BaseModel):
    tools_to_use: list[str]

# Enhanced structure info with complete metadata
class ProteinStructureInfo(BaseModel):
    """Complete protein structure information"""
    pdb_id: str
    title: str = ""
    method: str = ""
    resolution_A: float = 0.0
    r_work: float = 0.0
    r_free: float = 0.0
    space_group: str = ""
    deposition_date: str = ""
    organisms: List[str] = []
    protein_chains: List[str] = []
    ligands: List[str] = []
    entities: List[Dict[str, Any]] = []
    assembly: Dict[str, Any] = {}
    quality_score: str = ""
    sequence: str = ""
    sequence_length: int = 0
    molecule_type: str = ""
    score: float = 0.0

# Base model with comprehensive fields for all protein search tools
class BaseProteinSearchResult(BaseModel):
    """Base model with comprehensive fields for all protein search tool results"""
    tool_name: str
    success: bool = True
    execution_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    query_params: Dict[str, Any] = {}
    error_message: str = ""
    warnings: List[str] = []
    
    # Comprehensive results - no None values
    structures: List[ProteinStructureInfo] = []
    pdb_ids: List[str] = []
    total_count: int = 0
    returned_count: int = 0
    scores: Dict[str, float] = {}
    
    # Metadata about the search
    search_metadata: Dict[str, Any] = {}

# Individual tool result models with rich data

class SearchStructuresResult(BaseProteinSearchResult):
    """Results from search_structures_tool with comprehensive structure data"""
    tool_name: str = "search_structures_tool"
    
    # Tool-specific fields
    search_query: str = ""
    organism: str = ""
    method: str = ""
    max_resolution: float = 0.0
    
    # Enhanced results
    organisms_found: List[str] = []
    methods_found: List[str] = []
    resolution_range: Dict[str, float] = {"min": 0.0, "max": 0.0}

class SearchBySequenceResult(BaseProteinSearchResult):
    """Results from search_by_sequence_tool with sequence alignment data"""
    tool_name: str = "search_by_sequence_tool"
    
    # Tool-specific fields
    sequence: str = ""
    sequence_type: str = "protein"
    identity_cutoff: float = 0.5
    evalue_cutoff: float = 1.0
    
    # Enhanced results
    sequence_length: int = 0
    alignment_data: List[Dict[str, Any]] = []
    identity_scores: Dict[str, float] = {}
    evalue_scores: Dict[str, float] = {}

class SearchByStructureResult(BaseProteinSearchResult):
    """Results from search_by_structure_tool with structural similarity data"""
    tool_name: str = "search_by_structure_tool"
    
    # Tool-specific fields
    reference_pdb_ids: List[str] = []
    assembly_id: str = "1"
    match_type: str = "relaxed"
    
    # Enhanced results
    similarity_scores: Dict[str, float] = {}
    structural_matches: Dict[str, Dict[str, Any]] = {}
    by_reference: Dict[str, Any] = {}

class SearchByChemicalResult(BaseProteinSearchResult):
    """Results from search_by_chemical_tool with chemical compound data"""
    tool_name: str = "search_by_chemical_tool"
    
    # Tool-specific fields
    chemical_identifier: str = ""
    identifier_type: str = "SMILES"
    ligand_name: str = ""
    match_type: str = "graph-relaxed"
    
    # Enhanced results
    ligands_found: List[Dict[str, Any]] = []
    binding_sites: Dict[str, List[Dict[str, Any]]] = {}
    chemical_properties: Dict[str, Any] = {}

class GetHighQualityStructuresResult(BaseProteinSearchResult):
    """Results from get_high_quality_structures_tool with quality metrics"""
    tool_name: str = "get_high_quality_structures_tool"
    
    # Tool-specific fields
    max_resolution: float = 2.0
    max_r_work: float = 0.25
    max_r_free: float = 0.28
    method: str = "X-RAY DIFFRACTION"
    min_year: int = 2000
    
    # Enhanced results
    quality_distribution: Dict[str, int] = {}
    resolution_stats: Dict[str, float] = {}
    yearly_distribution: Dict[int, int] = {}

class StructureInfo(BaseModel):
    """Detailed information for a single structure"""
    pdb_id: str
    title: str = ""
    method: str = ""
    resolution_A: float = 0.0
    r_work: float = 0.0
    r_free: float = 0.0
    space_group: str = ""
    deposition_date: str = ""
    organisms: List[str] = []
    ligands: List[str] = []
    entities: List[Dict[str, Any]] = []
    assembly: Dict[str, Any] = {}
    quality_score: str = ""

class GetStructureDetailsResult(BaseProteinSearchResult):
    """Results from get_structure_details_tool with detailed structure information"""
    tool_name: str = "get_structure_details_tool"
    
    # Enhanced structure details
    structure_details: Dict[str, StructureInfo] = {}
    include_assembly: bool = True
    
    # Additional metadata
    structure_types: List[str] = []
    experimental_methods: List[str] = []
    organism_diversity: Dict[str, int] = {}

class SequenceInfo(BaseModel):
    """Sequence information for a structure entity"""
    pdb_id: str
    entity_id: str
    sequence: str = ""
    sequence_length: int = 0
    sequence_type: str = ""
    molecule_type: str = ""
    organism: str = ""
    description: str = ""

class GetSequencesResult(BaseProteinSearchResult):
    """Results from get_sequences_tool with sequence data"""
    tool_name: str = "get_sequences_tool"
    
    # Enhanced sequence data
    sequences: Dict[str, SequenceInfo] = {}
    entity_ids: List[str] = []
    
    # Additional metadata
    sequence_stats: Dict[str, Any] = {}
    length_distribution: Dict[str, int] = {}
    type_distribution: Dict[str, int] = {}

class ComparisonInfo(BaseModel):
    """Comparison information between two structures"""
    pdb_pair: str
    sequence_identity: float = 0.0
    length_difference: int = 0
    structural_similarity: float = 0.0
    comparison_note: str = ""
    rmsd: float = 0.0
    alignment_length: int = 0

class CompareStructuresResult(BaseProteinSearchResult):
    """Results from compare_structures_tool with comparison data"""
    tool_name: str = "compare_structures_tool"
    
    # Enhanced comparison data
    comparison_type: str = "both"
    comparisons: Dict[str, ComparisonInfo] = {}
    summary: Dict[str, Any] = {}
    
    # Additional metadata
    similarity_matrix: Dict[str, Dict[str, float]] = {}
    cluster_analysis: Dict[str, Any] = {}

class InteractionInfo(BaseModel):
    """Interaction information for a structure"""
    pdb_id: str
    protein_chains: List[str] = []
    ligands: List[str] = []
    interactions: List[Dict[str, Any]] = []
    quaternary_structure: Dict[str, Any] = {}
    binding_sites: List[Dict[str, Any]] = []
    interface_area: float = 0.0

class AnalyzeInteractionsResult(BaseProteinSearchResult):
    """Results from analyze_interactions_tool with interaction analysis"""
    tool_name: str = "analyze_interactions_tool"
    
    # Enhanced interaction data
    interaction_type: str = "all"
    interactions: Dict[str, InteractionInfo] = {}
    
    # Additional metadata
    interaction_summary: Dict[str, Any] = {}
    complex_types: Dict[str, int] = {}
    binding_partners: Dict[str, List[str]] = {}

class StructuralSummaryInfo(BaseModel):
    """Comprehensive summary for a structure"""
    pdb_id: str
    title: str = ""
    experimental: Dict[str, Any] = {}
    composition: Dict[str, Any] = {}
    biological_assembly: Dict[str, Any] = {}
    research_relevance: Dict[str, Any] = {}
    quality: Dict[str, Any] = {}
    organisms: List[str] = []
    functional_classification: str = ""
    research_applications: List[str] = []

class GetStructuralSummaryResult(BaseProteinSearchResult):
    """Results from get_structural_summary_tool with comprehensive summaries"""
    tool_name: str = "get_structural_summary_tool"
    
    # Enhanced summary data
    include_quality_metrics: bool = True
    summaries: Dict[str, StructuralSummaryInfo] = {}
    
    # Additional metadata
    research_trends: Dict[str, Any] = {}
    quality_overview: Dict[str, Any] = {}
    functional_categories: Dict[str, int] = {}

# Union type for all possible tool results
ProteinToolResult = Union[
    SearchStructuresResult,
    SearchBySequenceResult,
    SearchByStructureResult,
    SearchByChemicalResult,
    GetHighQualityStructuresResult,
    GetStructureDetailsResult,
    GetSequencesResult,
    CompareStructuresResult,
    AnalyzeInteractionsResult,
    GetStructuralSummaryResult
]

class ProteinSearchResponse(BaseModel):
    """Container for all protein search results"""
    query: str
    tool_results: List[ProteinToolResult] = []
    total_tools_used: int = 0
    successful_tools: int = 0
    failed_tools: int = 0
    total_execution_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True
    
    # Enhanced metadata
    search_summary: Dict[str, Any] = {}
    unique_structures: List[str] = []
    organism_coverage: Dict[str, int] = {}
    
    def get_all_pdb_ids(self) -> List[str]:
        """Get all unique PDB IDs from all tool results"""
        all_pdb_ids = set()
        for result in self.tool_results:
            if result.pdb_ids:
                all_pdb_ids.update(result.pdb_ids)
        return list(all_pdb_ids)
    
    def get_total_structures_found(self) -> int:
        """Get total count of unique structures found"""
        return len(self.get_all_pdb_ids())
    
    def get_summary(self) -> str:
        """Get a summary of all results"""
        total_unique = self.get_total_structures_found()
        return f"{self.total_tools_used} tools used, {total_unique} unique structures found"