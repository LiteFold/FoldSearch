from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class ToolsToUseResult(BaseModel):
    tools_to_use: list[str]

# Enhanced ligand info with complete metadata
class LigandInfo(BaseModel):
    """
    Complete ligand information model containing all relevant chemical and biological data.
    
    This model represents a comprehensive view of a chemical ligand/compound including:
    - Chemical identifiers (Name, SMILES, InChI, ChEMBL ID)
    - Molecular properties (dictionary of properties like formula, weight, charge)
    - Structure information (MOL file, 3D coordinates if available)
    
    Used throughout the ligand search system as the standard representation
    for chemical compounds and their associated metadata.
    """
    name: Optional[str] = None
    smiles: Optional[str] = None
    inchi: Optional[str] = None
    chembl_id: Optional[str] = None
    structure: Optional[str] = None  # MOL file contents
    properties: Dict[str, Any] = {}

    @classmethod
    def from_chembl(cls, chembl_data: Dict[str, Any]) -> "LigandInfo":
        """
        Create a LigandInfo instance from ChEMBL data dictionary.
        
        This method extracts relevant fields from the ChEMBL data structure
        and populates the LigandInfo model accordingly.
        
        Args:
            chembl_data (Dict[str, Any]): Dictionary containing ChEMBL compound data.
        
        Returns:
            LigandInfo: Populated ligand information model.
        """
        # Extract relevant fields from the ChEMBL data
        return LigandInfo(
            name=chembl_data.get('pref_name'),
            smiles=chembl_data.get('molecule_structures', {}).get('canonical_smiles'),
            inchi=chembl_data.get('molecule_structures', {}).get('standard_inchi'),
            chembl_id=chembl_data.get('molecule_chembl_id'),
            structure=chembl_data.get('molecule_structures', {}).get('molfile'),
            properties=chembl_data.get('molecule_properties', {})
        )

# Base model with comprehensive fields for all ligand search tools
class BaseLigandSearchResult(BaseModel):
    """
    Base result model providing comprehensive metadata for all ligand search operations.
    
    This abstract base class standardizes the response format across all ligand search tools.
    It includes:
    - Execution metadata (timing, success status, errors)
    - Search parameters and query context
    - Result counts and pagination info
    - Warning and error message handling
    - Extensible metadata dictionary for tool-specific data
    
    All specific tool result models inherit from this base to ensure consistency
    in response structure and enable unified result processing across the system.
    
    Attributes:
        tool_name: Identifier for the specific tool that generated results
        success: Boolean indicating if the operation completed successfully
        execution_time: Time taken for the operation in seconds
        timestamp: When the operation was performed
        query_params: Original parameters passed to the search function
        error_message: Human-readable error description if operation failed
        warnings: List of non-fatal warnings encountered during execution
        ligands: List of LigandInfo objects representing found compounds
        total_count: Total number of matches found (may exceed returned_count)
        search_metadata: Tool-specific metadata and search context
    """
    tool_name: str
    success: bool = True
    execution_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    query_params: Dict[str, Any] = {}
    error_message: str = ""
    warnings: List[str] = []
    
    # Comprehensive results - no None values
    ligands: List[LigandInfo] = []
    total_count: int = 0
    
    # Metadata about the search
    search_metadata: Dict[str, Any] = {}

# Individual tool result models with rich data

class SearchLigandsToolResult(BaseLigandSearchResult):
    """
    Results from the general ligand search tool supporting multiple search types.
    
    This model extends BaseLigandSearchResult with specific fields for general ligand
    searches by name, SMILES, InChI, molecular formula, or ChEMBL ID. It tracks the search strategy
    used and provides enhanced metadata about the types of matches found.
    
    The tool supports both exact and fuzzy matching strategies, making it versatile
    for initial compound discovery and specific identifier lookups.
    
    Additional Attributes:
        search_query: The original search term provided by the user
        search_type: Type of search performed ("name", "smiles", "inchi", "formula", "chembl_id")
        exact_match: Whether exact matching was used (vs fuzzy matching)
    """
    tool_name: str = "search_ligands_tool"
    
    # Tool-specific fields
    search_query: str = ""
    search_type: str = "name"  # name, smiles, inchi, formula, chembl_id
    exact_match: bool = False

# Response wrapper
class LigandSearchResponse(BaseModel):
    """Main response model for ligand search operations"""
    success: bool = True
    results: List[BaseLigandSearchResult] = []
    total_execution_time: float = 0.0
    tools_used: List[str] = []
    error_message: str = ""
    summary: Dict[str, Any] = {}
    
