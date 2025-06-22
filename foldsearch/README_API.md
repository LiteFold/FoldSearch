# FoldSearch API Documentation

A comprehensive FastAPI-based web service that combines web research and protein structure search capabilities through intelligent agent orchestration. Returns tool-specific results with comprehensive structural data and no null values.

## Table of Contents

- [System Architecture](#system-architecture)
- [Enhanced Workflow](#enhanced-workflow)
- [API Endpoints](#api-endpoints)
- [Tool-Specific Results Format](#tool-specific-results-format)
- [Comprehensive Data Models](#comprehensive-data-models)
- [Protein Search Tools](#protein-search-tools)
- [Response Examples](#response-examples)
- [Integration Guide](#integration-guide)
- [Running the Service](#running-the-service)

---

## System Architecture

FoldSearch API consists of three main components with enhanced data fetching:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   FastAPI       │    │  Web Research    │    │  Protein Search     │
│   Main Server   │───▶│  Agent           │    │  Agent              │
│                 │    │                  │    │                     │
│ - Tool-Specific │    │ - Research       │    │ - 10 Search Tools   │
│ - Results       │    │ - Paper Finding  │    │ - Auto Data Fetch   │
│ - Rich Metadata │    │ - Query Gen      │    │ - Sequence Analysis │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

### Core Enhancement Features

✅ **Tool-Specific Results**: Each tool returns separate, identifiable results  
✅ **Comprehensive Data**: Automatic fetching of titles, sequences, organisms, resolution, etc.  
✅ **No Null Values**: All fields populated with meaningful data or appropriate defaults  
✅ **Rich Metadata**: Quality metrics, statistics, and enhanced structural information  
✅ **Parallel Execution**: All tools run concurrently for maximum performance

---

## Enhanced Workflow

### New Search Flow with Comprehensive Data

1. **Request Processing**

   ```python
   {
     "query": "CRISPR Cas9 high fidelity variants",
     "include_web": true,
     "include_protein": true,
     "max_protein_queries": 5
   }
   ```

2. **Phase 1: Web Research**

   - Executes web search using OpenAI
   - Finds relevant research papers
   - Generates protein-specific follow-up queries

3. **Phase 2: Protein Search with Auto-Enhancement**

   - Uses follow-up queries for targeted protein searches
   - **Automatically fetches comprehensive data for each PDB ID found**:
     - Structure details (title, method, resolution, quality metrics)
     - Sequences (full protein sequences, lengths, types)
     - Organism information (species, taxonomy)
     - Ligand binding data (chemical compounds, binding sites)
     - Assembly information (quaternary structure, oligomeric states)
   - Runs multiple tools concurrently
   - Each tool result includes rich metadata and statistics

4. **Phase 3: Tool-Specific Result Aggregation**
   - Returns results as `{"tool_name": tool_result}` format
   - Each tool maintains its own comprehensive data
   - No merging or data loss between tools
   - Statistics and metadata preserved per tool

---

## API Endpoints

### `POST /search` - Combined Search Endpoint

**Purpose**: Performs both web research and protein structure search with intelligent query enhancement.

**Request Model:**

```typescript
interface SearchRequest {
  query: string; // Required: Search query
  include_web?: boolean; // Optional: Include web results (default: true)
  include_protein?: boolean; // Optional: Include protein results (default: true)
  max_protein_queries?: number; // Optional: Max follow-up queries (default: 5)
}
```

**Response Model:**

```typescript
interface SearchResponse {
  success: boolean;
  message: string;
  data: CombinedSearchResult;
  execution_time: number;
  timestamp: string;
}
```

### `POST /web-search` - Web-Only Search Endpoint

**Purpose**: Performs web research only using the Web Research Agent to find relevant papers and generate follow-up queries.

**Request Model:**

```typescript
interface WebSearchRequest {
  query: string; // Required: Search query for web research
}
```

**Response Model:**

```typescript
interface WebSearchResponse {
  success: boolean;
  message: string;
  data: WebResearchAgentModel | null;
  execution_time: number;
  timestamp: string;
}
```

**WebResearchAgentModel Structure:**

```typescript
interface WebResearchAgentModel {
  query: string;
  raw_result: string;
  research_paper: {
    search_result: Array<{
      title: string;
      url: string;
      abstract: string;
    }>;
  };
  upnext_queries: string[]; // Follow-up queries for protein search
}
```

### `POST /protein-search` - Protein-Only Search Endpoint

**Purpose**: Performs comprehensive protein structure search using all 10 protein search tools with enhanced data fetching.

**Request Model:**

```typescript
interface ProteinSearchRequest {
  query: string; // Required: Search query for protein structures
}
```

**Response Model:**

```typescript
interface ProteinOnlySearchResponse {
  success: boolean;
  message: string;
  data: ProteinSearchResponse | null;
  execution_time: number;
  timestamp: string;
}
```

**ProteinSearchResponse Structure:**

```typescript
interface ProteinSearchResponse {
  query: string;
  success: boolean;
  tool_results: Array<{
    tool_name: string;
    success: boolean;
    structures: ProteinStructureInfo[];
    execution_time: number;
    // ... other tool-specific fields
  }>;
  total_execution_time: number;
  timestamp: string;
}
```

### `GET /health` - Health Check

Returns system health status and timestamp.

### `GET /` - API Information

Returns API metadata and available endpoints including all three search endpoints.

---

## Endpoint Usage Guidelines

### When to Use Each Endpoint

#### `POST /search` - Combined Search

**Best for**: Research workflows where you need both literature context and structural data

- **Use when**: Starting a new research project or comprehensive analysis
- **Advantages**:
  - Web search provides research context and generates protein-specific queries
  - Protein search uses enhanced queries for more targeted results
  - Single request provides complete research picture
- **Time**: 45-90 seconds for comprehensive results
- **Example queries**:
  - "CRISPR Cas9 high fidelity variants"
  - "Alzheimer's disease tau protein aggregation inhibitors"
  - "COVID-19 spike protein receptor binding domain mutations"

#### `POST /web-search` - Web Research Only

**Best for**: Literature review, finding recent papers, understanding research trends

- **Use when**: Need quick literature overview or research paper discovery
- **Advantages**:
  - Fast execution (5-15 seconds)
  - Generates follow-up queries for subsequent protein searches
  - Focuses on latest research findings
- **Time**: 5-15 seconds
- **Example queries**:
  - "latest advances in protein folding prediction 2024"
  - "machine learning drug discovery computational methods"
  - "CRISPR off-target reduction strategies review"

#### `POST /protein-search` - Protein Structures Only

**Best for**: Structural biology analysis, protein engineering, drug design

- **Use when**: Need comprehensive structural data without literature context
- **Advantages**:
  - Direct access to all 10 protein search tools
  - Comprehensive structural metadata
  - Optimized for structural analysis workflows
- **Time**: 30-60 seconds
- **Example queries**:
  - "human insulin receptor tyrosine kinase domain"
  - "beta-lactamase enzyme active site structures"
  - "membrane protein crystal structures resolution better than 2.5A"

### Performance Comparison

| Endpoint          | Execution Time | Tools Used       | Best For               |
| ----------------- | -------------- | ---------------- | ---------------------- |
| `/search`         | 45-90s         | Web + 10 Protein | Comprehensive research |
| `/web-search`     | 5-15s          | Web only         | Literature review      |
| `/protein-search` | 30-60s         | 10 Protein only  | Structural analysis    |

---

## Tool-Specific Results Format

### New Result Structure

The API now returns results in a tool-specific format:

```python
class CombinedSearchResult(BaseModel):
    query: str
    tool_results: Dict[str, Any] = {}  // Tool name -> Tool result
    search_type: str                   // "combined", "web", "protein"
    timestamp: datetime
    success: bool = True
    error_message: str = ""

    // Enhanced statistics
    total_tools_used: int = 0
    successful_tools: int = 0
    failed_tools: int = 0
    total_execution_time: float = 0.0
```

### Example Tool Results Dictionary

```json
{
  "tool_results": {
    "web_search_tool": {
      /* web search result */
    },
    "search_structures_tool": {
      /* comprehensive structure data */
    },
    "search_by_sequence_tool": {
      /* sequence alignment data */
    },
    "get_structure_details_tool": {
      /* detailed metadata */
    },
    "get_sequences_tool": {
      /* full sequences */
    },
    "analyze_interactions_tool": {
      /* binding analysis */
    }
  }
}
```

---

## Comprehensive Data Models

### Enhanced Base Protein Search Result

All protein search tools now return comprehensive data with no null values:

```python
class BaseProteinSearchResult(BaseModel):
    // Core identification
    tool_name: str
    success: bool = True
    execution_time: float = 0.0
    timestamp: datetime
    query_params: Dict[str, Any] = {}
    error_message: str = ""
    warnings: List[str] = []

    // Comprehensive results - no None values
    structures: List[ProteinStructureInfo] = []  // NEW: Full structure objects
    pdb_ids: List[str] = []
    total_count: int = 0
    returned_count: int = 0
    scores: Dict[str, float] = {}
    search_metadata: Dict[str, Any] = {}
```

### Enhanced Structure Information

Every PDB structure now includes comprehensive data:

```python
class ProteinStructureInfo(BaseModel):
    // Basic identification
    pdb_id: str
    title: str = ""                    // Real structure title
    method: str = ""                   // Experimental method
    score: float = 0.0                 // Relevance score

    // Quality metrics
    resolution_A: float = 0.0          // Resolution in Angstroms
    r_work: float = 0.0               // R-work value
    r_free: float = 0.0               // R-free value
    space_group: str = ""             // Crystal space group
    deposition_date: str = ""         // PDB deposition date
    quality_score: str = ""           // Calculated quality assessment

    // Biological information
    organisms: List[str] = []         // Species information
    protein_chains: List[str] = []    // Chain identifiers
    ligands: List[str] = []           // Bound molecules
    entities: List[Dict[str, Any]] = [] // Detailed entity information
    assembly: Dict[str, Any] = {}     // Quaternary structure

    // Sequence data
    sequence: str = ""                // Full protein sequence
    sequence_length: int = 0          // Sequence length
    molecule_type: str = ""           // Protein/DNA/RNA type
```

---

## Protein Search Tools

### Comprehensive Tool Descriptions

Each tool now returns rich, structured data with comprehensive metadata:

### 1. Search Structures Tool

**Purpose**: Text-based structure search with enhanced metadata

```python
class SearchStructuresResult(BaseProteinSearchResult):
    tool_name: str = "search_structures_tool"

    // Search parameters
    search_query: str = ""
    organism: str = ""
    method: str = ""
    max_resolution: float = 0.0

    // Enhanced results with real data
    organisms_found: List[str] = []           // All organisms in results
    methods_found: List[str] = []             // All experimental methods
    resolution_range: Dict[str, float] = {}   // Min/max resolution statistics
```

**Enhanced Data Includes**:

- ✅ Real structure titles and descriptions
- ✅ Experimental methods (X-RAY, NMR, EM)
- ✅ Resolution statistics and quality metrics
- ✅ Organism diversity analysis
- ✅ Full sequences for each structure

### 2. Search by Sequence Tool

**Purpose**: Sequence similarity search with alignment data

```python
class SearchBySequenceResult(BaseProteinSearchResult):
    tool_name: str = "search_by_sequence_tool"

    // Search parameters
    sequence: str = ""
    sequence_type: str = "protein"
    identity_cutoff: float = 0.5
    evalue_cutoff: float = 1.0

    // Enhanced results
    sequence_length: int = 0
    alignment_data: List[Dict[str, Any]] = []    // Alignment information
    identity_scores: Dict[str, float] = {}       // Sequence identity per PDB
    evalue_scores: Dict[str, float] = {}         // E-values per match
```

**Enhanced Data Includes**:

- ✅ Detailed alignment information
- ✅ Identity and E-value scores for each match
- ✅ Full sequences of matched structures
- ✅ Sequence length distribution analysis

### 3. Search by Structure Tool

**Purpose**: 3D structural similarity search

```python
class SearchByStructureResult(BaseProteinSearchResult):
    tool_name: str = "search_by_structure_tool"

    // Search parameters
    reference_pdb_ids: List[str] = []
    assembly_id: str = "1"
    match_type: str = "relaxed"

    // Enhanced results
    similarity_scores: Dict[str, float] = {}           // Structural similarity scores
    structural_matches: Dict[str, Dict[str, Any]] = {} // Detailed match information
    by_reference: Dict[str, Any] = {}                  // Results grouped by reference
```

**Enhanced Data Includes**:

- ✅ Structural similarity scores and RMSD values
- ✅ Detailed comparison metrics
- ✅ Conformational analysis data
- ✅ Assembly and quaternary structure information

### 4. Search by Chemical Tool

**Purpose**: Chemical compound and ligand search

```python
class SearchByChemicalResult(BaseProteinSearchResult):
    tool_name: str = "search_by_chemical_tool"

    // Search parameters
    chemical_identifier: str = ""
    identifier_type: str = "SMILES"
    ligand_name: str = ""
    match_type: str = "graph-relaxed"

    // Enhanced results
    ligands_found: List[Dict[str, Any]] = []          // Detailed ligand information
    binding_sites: Dict[str, List[Dict[str, Any]]] = {} // Binding site analysis
    chemical_properties: Dict[str, Any] = {}           // Chemical property analysis
```

**Enhanced Data Includes**:

- ✅ Detailed ligand binding information
- ✅ Binding site coordinates and analysis
- ✅ Chemical property comparisons
- ✅ Drug-target interaction data

### 5. Get High Quality Structures Tool

**Purpose**: High-resolution structure filtering with quality analysis

```python
class GetHighQualityStructuresResult(BaseProteinSearchResult):
    tool_name: str = "get_high_quality_structures_tool"

    // Quality parameters
    max_resolution: float = 2.0
    max_r_work: float = 0.25
    max_r_free: float = 0.28
    method: str = "X-RAY DIFFRACTION"
    min_year: int = 2000

    // Enhanced quality analysis
    quality_distribution: Dict[str, int] = {}     // Quality category counts
    resolution_stats: Dict[str, float] = {}       // Resolution statistics
    yearly_distribution: Dict[int, int] = {}      // Publication year distribution
```

**Enhanced Data Includes**:

- ✅ Comprehensive quality metrics analysis
- ✅ Resolution and R-factor statistics
- ✅ Temporal distribution of structures
- ✅ Quality scoring and ranking

### 6. Get Structure Details Tool

**Purpose**: Comprehensive structural metadata

```python
class GetStructureDetailsResult(BaseProteinSearchResult):
    tool_name: str = "get_structure_details_tool"

    // Enhanced structure details
    structure_details: Dict[str, StructureInfo] = {}
    include_assembly: bool = True

    // Additional metadata
    structure_types: List[str] = []               // Types of structures
    experimental_methods: List[str] = []          // All methods used
    organism_diversity: Dict[str, int] = {}       // Organism frequency analysis
```

**Enhanced Data Includes**:

- ✅ Complete experimental details
- ✅ Assembly and symmetry information
- ✅ Entity composition analysis
- ✅ Quality assessment and validation

### 7. Get Sequences Tool

**Purpose**: Sequence retrieval with comprehensive analysis

```python
class GetSequencesResult(BaseProteinSearchResult):
    tool_name: str = "get_sequences_tool"

    // Enhanced sequence data
    sequences: Dict[str, SequenceInfo] = {}
    entity_ids: List[str] = []

    // Additional metadata
    sequence_stats: Dict[str, Any] = {}           // Sequence statistics
    length_distribution: Dict[str, int] = {}      // Length distribution
    type_distribution: Dict[str, int] = {}        // Molecule type distribution
```

**Enhanced Data Includes**:

- ✅ Full protein sequences with organism information
- ✅ Sequence length and composition analysis
- ✅ Molecular type classification
- ✅ Entity relationship mapping

### 8. Compare Structures Tool

**Purpose**: Multi-structure comparison analysis

```python
class CompareStructuresResult(BaseProteinSearchResult):
    tool_name: str = "compare_structures_tool"

    // Enhanced comparison data
    comparison_type: str = "both"
    comparisons: Dict[str, ComparisonInfo] = {}
    summary: Dict[str, Any] = {}

    // Additional metadata
    similarity_matrix: Dict[str, Dict[str, float]] = {} // Pairwise similarity
    cluster_analysis: Dict[str, Any] = {}               // Clustering results
```

**Enhanced Data Includes**:

- ✅ Pairwise structural and sequence comparisons
- ✅ RMSD values and alignment statistics
- ✅ Evolutionary relationship analysis
- ✅ Cluster analysis and phylogenetic insights

### 9. Analyze Interactions Tool

**Purpose**: Protein-protein and protein-ligand interaction analysis

```python
class AnalyzeInteractionsResult(BaseProteinSearchResult):
    tool_name: str = "analyze_interactions_tool"

    // Enhanced interaction data
    interaction_type: str = "all"
    interactions: Dict[str, InteractionInfo] = {}

    // Additional metadata
    interaction_summary: Dict[str, Any] = {}      // Summary statistics
    complex_types: Dict[str, int] = {}            // Complex type frequencies
    binding_partners: Dict[str, List[str]] = {}   // Binding partner analysis
```

**Enhanced Data Includes**:

- ✅ Detailed binding site analysis
- ✅ Interface area calculations
- ✅ Interaction network mapping
- ✅ Complex assembly information

### 10. Get Structural Summary Tool

**Purpose**: Comprehensive research overview

```python
class GetStructuralSummaryResult(BaseProteinSearchResult):
    tool_name: str = "get_structural_summary_tool"

    // Enhanced summary data
    include_quality_metrics: bool = True
    summaries: Dict[str, StructuralSummaryInfo] = {}

    // Additional metadata
    research_trends: Dict[str, Any] = {}          // Research trend analysis
    quality_overview: Dict[str, Any] = {}         // Quality overview
    functional_categories: Dict[str, int] = {}    // Functional classification
```

**Enhanced Data Includes**:

- ✅ Research relevance scoring
- ✅ Functional classification
- ✅ Drug discovery applications
- ✅ Publication and citation analysis

---

## Response Examples

### Complete Enhanced Search Response

```json
{
  "success": true,
  "message": "Search completed successfully. 8 web results; Protein: 6 tools used, 150 unique structures found",
  "data": {
    "query": "CRISPR Cas9 high fidelity variants",
    "tool_results": {
      "web_search_tool": {
        "query": "CRISPR Cas9 high fidelity variants",
        "raw_result": "Research findings indicate several high-fidelity Cas9 variants...",
        "research_paper": {
          "search_result": [
            {
              "title": "High-fidelity CRISPR-Cas9 variants with undetectable genome-wide off-targets",
              "url": "https://www.nature.com/articles/nature17946",
              "abstract": "The RNA-guided Cas9 nuclease from Streptococcus pyogenes..."
            }
          ]
        },
        "upnext_queries": [
          "SpCas9 high fidelity variants crystal structure",
          "eSpCas9 Cas9-HF1 structural differences",
          "CRISPR Cas9 PAM recognition mechanism"
        ]
      },
      "search_structures_tool": {
        "tool_name": "search_structures_tool",
        "success": true,
        "execution_time": 2.45,
        "timestamp": "2025-01-21T10:30:15.123456",
        "query_params": {
          "query": "SpCas9 high fidelity variants",
          "limit": 50
        },
        "error_message": "",
        "warnings": [],
        "structures": [
          {
            "pdb_id": "5F9R",
            "title": "Crystal structure of Cas9 in complex with guide RNA and target DNA",
            "method": "X-RAY DIFFRACTION",
            "resolution_A": 2.5,
            "r_work": 0.19,
            "r_free": 0.23,
            "space_group": "P 21 21 21",
            "deposition_date": "2015-12-23",
            "organisms": ["Streptococcus pyogenes"],
            "protein_chains": ["A", "B"],
            "ligands": ["MG", "ZN"],
            "entities": [
              {
                "entity_id": "1",
                "description": "CRISPR-associated endonuclease Cas9",
                "sequence_length": 1368,
                "molecule_type": "protein",
                "organism": "Streptococcus pyogenes"
              }
            ],
            "assembly": {
              "oligomeric_state": "hetero-trimeric",
              "oligomeric_count": 3
            },
            "quality_score": "Excellent (high resolution, good R-factors)",
            "sequence": "MDKKYSIGLDIGTNSVGWAVITDEYKVPSKKFKVLGNTDRHSIKKNLIGALLFDSGETAEATRLKRTARRRYTRRKNRICYLQEIFSNEMAKVDDSFFHRLEESFLVEEDKKHERHPIFGNIVDEVAYHEKYPTIYHLRKKLVDSTDKADLRLIYLALAHMIKFRGHFLIEGDLNPDNSDVDKLFIQLVQTYNQLFEENPINASGVDAKAILSARLSKSRRLENLIAQLPGEKKNGLFGNLIALSLGLTPNFKSNFDLAEDAKLQLSKDTYDDDLDNLLAQIGDQYADLFLAAKNLSDAILLSDILRVNTEITKAPLSASMIKRYDEHHQDLTLLKALVRQQLPEKYKEIFFDQSKNGYAGYIDGGASQEEFYKFIKPILEKMDGTEELLVKLNREDLLRKQRTFDNGSIPHQIHLGELHAILRRQEDFYPFLKDNREKIEKILTFRIPYYVGPLARGNSRFAWMTRKSEETITPWNFEEVVDKGASAQSFIERMTNFDKNLPNEKVLPKHSLLYEYFTVYNELTKVKYVTEGMRKPAFLSGEQKKAIVDLLFKTNRKVTVKQLKEDYFKKIECFDSVEISGVEDRFNASLGTYHDLLKIIKDKDFLDNEENEDILEDIVLTLTLFEDREMIEERLKTYAHLFDDKVMKQLKRRRYTGWGRLSRKLINGIRDKQSGKTILDFLKSDGFANRNFMQLIHDDSLTFKEDIQKAQVSGQGDSLHEHIANLAGSPAIKKGILQTVKVVDELVKVMGRHKPENIVIEMARENQTTQKGQKNSRERMKRIEEGIKELGSQILKEHPVENTQLQNEKLYLYYLQNGRDMYVDQELDINRLSDYDVDHIVPQSFLKDDSIDNKVLTRSDKNRGKSDNVPSEEVVKKMKNYWRQLLNAKLITQRKFDNLTKAERGGLSELDKAGFIKRQLVETRQITKHVAQILDSRMNTKYDENDKLIREVKVITLKSKLVSDFRKDFQFYKVREINNYHHAHDAYLNAVVGTALIKKYPKLESEFVYGDYKVYDVRKMIAKSEQEIGKATAKYFFYSNIMNFFKTEITLANGEIRKRPLIETNGETGEIVWDKGRDFATVRKVLSMPQVNIVKKTEVQTGGFSKESILPKRNSDKLIARKKDWDPKKYGGFDSPTVAYSVLVVAKVEKGKSKKLKSVKELLGITIMERSSFEKNPIDFLEAKGYKEVKKDLIIKLPKYSLFELENGRKRMLASAGELQKGNELALPSKYVNFLYLASHYEKLKGSPEDNEQKQLFVEQHKHYLDEIIEQISEFSKRVILADANLDKVLSAYNKHRDKPIREQAENIIHLFTLTNLGAPAAFKYFDTTIDRKRYTSTKEVLDATLIHQSITGLYETRIDLSQLGGD",
            "sequence_length": 1368,
            "molecule_type": "protein",
            "score": 1.0
          }
        ],
        "pdb_ids": ["5F9R", "6O0Y", "7K7X"],
        "total_count": 87,
        "returned_count": 50,
        "scores": {
          "5F9R": 1.0,
          "6O0Y": 0.95,
          "7K7X": 0.92
        },
        "search_metadata": {
          "search_completed": true,
          "quality_metrics": {
            "avg_score": 0.96,
            "max_score": 1.0,
            "min_score": 0.85,
            "score_range": 0.15
          }
        },
        "search_query": "SpCas9 high fidelity variants",
        "organism": "",
        "method": "",
        "max_resolution": 0.0,
        "organisms_found": ["Streptococcus pyogenes", "Francisella novicida"],
        "methods_found": ["X-RAY DIFFRACTION", "ELECTRON MICROSCOPY"],
        "resolution_range": {
          "min": 2.2,
          "max": 3.8
        }
      },
      "get_high_quality_structures_tool": {
        "tool_name": "get_high_quality_structures_tool",
        "success": true,
        "execution_time": 1.89,
        "structures": [
          {
            "pdb_id": "6O0Y",
            "title": "Cryo-EM structure of Cas9 in complex with guide RNA",
            "method": "ELECTRON MICROSCOPY",
            "resolution_A": 3.2,
            "r_work": 0.0,
            "r_free": 0.0,
            "organisms": ["Streptococcus pyogenes"],
            "sequence_length": 1368,
            "quality_score": "Good (cryo-EM structure)"
          }
        ],
        "max_resolution": 2.0,
        "max_r_work": 0.25,
        "max_r_free": 0.28,
        "method": "X-RAY DIFFRACTION",
        "min_year": 2000,
        "quality_distribution": {
          "excellent": 15,
          "good": 25,
          "acceptable": 10
        },
        "resolution_stats": {
          "mean": 2.8,
          "min": 2.2,
          "max": 3.8,
          "count": 50
        },
        "yearly_distribution": {
          "2015": 5,
          "2016": 8,
          "2017": 12,
          "2018": 15,
          "2019": 10
        }
      },
      "search_by_chemical_tool": {
        "tool_name": "search_by_chemical_tool",
        "success": true,
        "execution_time": 3.12,
        "chemical_identifier": "CC(C)C1=NC(=CS1)C2=CN=C(N=C2N)N",
        "identifier_type": "SMILES",
        "ligands_found": [
          {
            "pdb_id": "5F9R",
            "ligand_name": "MG",
            "binding_context": "Found in Crystal structure of Cas9 in complex with guide RNA and target DNA"
          }
        ],
        "binding_sites": {
          "5F9R": [
            {
              "ligand": "MG",
              "chains": ["A", "B"]
            }
          ]
        },
        "chemical_properties": {
          "molecular_weight": 245.3,
          "logP": 1.2,
          "hbd": 2,
          "hba": 4
        }
      }
    },
    "search_type": "combined",
    "timestamp": "2025-01-21T10:30:15.123456",
    "success": true,
    "error_message": "",
    "total_tools_used": 6,
    "successful_tools": 6,
    "failed_tools": 0,
    "total_execution_time": 45.67
  },
  "execution_time": 45.67,
  "timestamp": "2025-01-21T10:30:15.123456"
}
```

---

## Integration Guide

### TypeScript/React Example with Enhanced Data Handling

```typescript
interface EnhancedSearchResponse {
  success: boolean;
  message: string;
  data: {
    query: string;
    tool_results: Record<string, any>;
    search_type: string;
    total_tools_used: number;
    successful_tools: number;
    failed_tools: number;
  };
  execution_time: number;
  timestamp: string;
}

interface WebSearchResponse {
  success: boolean;
  message: string;
  data: {
    query: string;
    raw_result: string;
    research_paper: {
      search_result: Array<{
        title: string;
        url: string;
        abstract: string;
      }>;
    };
    upnext_queries: string[];
  } | null;
  execution_time: number;
  timestamp: string;
}

interface ProteinSearchResponse {
  success: boolean;
  message: string;
  data: {
    query: string;
    success: boolean;
    tool_results: any[];
    total_execution_time: number;
  } | null;
  execution_time: number;
  timestamp: string;
}

export const useSearchAPI = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  // Combined search (web + protein)
  const combinedSearch = async (query: string) => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          include_web: true,
          include_protein: true,
          max_protein_queries: 8,
        }),
      });
      const data: EnhancedSearchResponse = await response.json();
      setResult(data);

      // Access tool-specific results
      if (data.success) {
        const toolResults = data.data.tool_results;

        // Process web results
        if (toolResults.web_search_tool) {
          console.log(
            "Web papers found:",
            toolResults.web_search_tool.research_paper.search_result.length
          );
        }

        // Process protein structure results
        Object.entries(toolResults).forEach(([toolName, toolResult]) => {
          if (toolName !== "web_search_tool" && toolResult.structures) {
            console.log(
              `${toolName} found ${toolResult.structures.length} structures`
            );

            // Access comprehensive structure data
            toolResult.structures.forEach((structure) => {
              console.log(`PDB ${structure.pdb_id}: ${structure.title}`);
              console.log(`Resolution: ${structure.resolution_A}Å`);
              console.log(`Organisms: ${structure.organisms.join(", ")}`);
              console.log(`Sequence length: ${structure.sequence_length}`);
            });
          }
        });
      }
    } catch (error) {
      console.error("Combined search failed:", error);
    } finally {
      setLoading(false);
    }
  };

  // Web-only search
  const webSearch = async (query: string) => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/web-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data: WebSearchResponse = await response.json();
      setResult(data);

      if (data.success && data.data) {
        console.log(
          "Web search completed:",
          data.data.research_paper.search_result.length,
          "papers found"
        );
        console.log("Follow-up queries:", data.data.upnext_queries);

        // Process research papers
        data.data.research_paper.search_result.forEach((paper, index) => {
          console.log(`Paper ${index + 1}: ${paper.title}`);
          console.log(`URL: ${paper.url}`);
          console.log(`Abstract: ${paper.abstract.substring(0, 200)}...`);
        });
      }
    } catch (error) {
      console.error("Web search failed:", error);
    } finally {
      setLoading(false);
    }
  };

  // Protein-only search
  const proteinSearch = async (query: string) => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/protein-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data: ProteinSearchResponse = await response.json();
      setResult(data);

      if (data.success && data.data) {
        console.log(
          `Protein search completed with ${data.data.tool_results.length} tools`
        );

        // Process each tool result
        data.data.tool_results.forEach((toolResult) => {
          if (toolResult.success && toolResult.structures) {
            console.log(
              `${toolResult.tool_name}: ${toolResult.structures.length} structures found`
            );

            // Process structures from this tool
            toolResult.structures.forEach((structure) => {
              console.log(`  - ${structure.pdb_id}: ${structure.title}`);
              console.log(`    Resolution: ${structure.resolution_A}Å`);
              console.log(
                `    Organisms: ${structure.organisms?.join(", ") || "N/A"}`
              );
            });
          }
        });
      }
    } catch (error) {
      console.error("Protein search failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return {
    combinedSearch,
    webSearch,
    proteinSearch,
    loading,
    result,
  };
};
```

### Python Client Example for Enhanced Data

```python
import requests
from typing import Dict, List, Any

def enhanced_combined_search(query: str) -> Dict[str, Any]:
    """
    Perform enhanced combined search with comprehensive data retrieval
    """
    response = requests.post('http://localhost:8000/search', json={
        'query': query,
        'include_web': True,
        'include_protein': True,
        'max_protein_queries': 8
    })

    if response.status_code == 200:
        data = response.json()
        if data['success']:
            return process_enhanced_results(data['data'])
        else:
            print(f"Combined search failed: {data['message']}")
    return {}

def web_only_search(query: str) -> Dict[str, Any]:
    """
    Perform web-only search to find research papers and generate follow-up queries
    """
    response = requests.post('http://localhost:8000/web-search', json={
        'query': query
    })

    if response.status_code == 200:
        data = response.json()
        if data['success'] and data['data']:
            result = data['data']
            return {
                'query': result['query'],
                'papers_found': len(result['research_paper']['search_result']),
                'papers': result['research_paper']['search_result'],
                'follow_up_queries': result['upnext_queries'],
                'execution_time': data['execution_time']
            }
        else:
            print(f"Web search failed: {data['message']}")
    return {}

def protein_only_search(query: str) -> Dict[str, Any]:
    """
    Perform protein-only search using all protein structure tools
    """
    response = requests.post('http://localhost:8000/protein-search', json={
        'query': query
    })

    if response.status_code == 200:
        data = response.json()
        if data['success'] and data['data']:
            result = data['data']
            return process_protein_results(result)
        else:
            print(f"Protein search failed: {data['message']}")
    return {}

def process_protein_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process protein-only search results
    """
    analysis = {
        'query': results.get('query', ''),
        'total_tools_used': len(results.get('tool_results', [])),
        'successful_tools': 0,
        'total_structures': set(),
        'organisms': set(),
        'methods': set(),
        'sequences': [],
        'ligands': set(),
        'quality_metrics': [],
        'tool_breakdown': {}
    }

    # Process each tool result
    for tool_result in results.get('tool_results', []):
        tool_name = tool_result.get('tool_name', 'unknown')

        if tool_result.get('success', False):
            analysis['successful_tools'] += 1

            structures = tool_result.get('structures', [])
            analysis['tool_breakdown'][tool_name] = {
                'success': True,
                'structures_found': len(structures),
                'execution_time': tool_result.get('execution_time', 0)
            }

            for structure in structures:
                # Collect comprehensive data
                analysis['total_structures'].add(structure.get('pdb_id', ''))
                analysis['organisms'].update(structure.get('organisms', []))
                if structure.get('method'):
                    analysis['methods'].add(structure['method'])
                if structure.get('sequence'):
                    analysis['sequences'].append({
                        'pdb_id': structure['pdb_id'],
                        'sequence': structure['sequence'],
                        'length': structure.get('sequence_length', 0)
                    })
                analysis['ligands'].update(structure.get('ligands', []))

                if structure.get('resolution_A', 0) > 0:
                    analysis['quality_metrics'].append({
                        'pdb_id': structure['pdb_id'],
                        'resolution': structure['resolution_A'],
                        'r_work': structure.get('r_work', 0),
                        'r_free': structure.get('r_free', 0)
                    })
        else:
            analysis['tool_breakdown'][tool_name] = {
                'success': False,
                'error': tool_result.get('error_message', 'Unknown error')
            }

    # Convert sets to lists for JSON serialization
    analysis['total_structures'] = list(analysis['total_structures'])
    analysis['organisms'] = list(analysis['organisms'])
    analysis['methods'] = list(analysis['methods'])
    analysis['ligands'] = list(analysis['ligands'])

    return analysis

def process_enhanced_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process tool-specific results with comprehensive data
    """
    tool_results = results.get('tool_results', {})
    analysis = {
        'total_structures': set(),
        'organisms': set(),
        'methods': set(),
        'sequences': [],
        'ligands': set(),
        'quality_metrics': []
    }

    # Process each tool result
    for tool_name, tool_result in tool_results.items():
        if tool_name == 'web_search_tool':
            continue

        if hasattr(tool_result, 'get') and tool_result.get('structures'):
            for structure in tool_result['structures']:
                # Collect comprehensive data
                analysis['total_structures'].add(structure['pdb_id'])
                analysis['organisms'].update(structure.get('organisms', []))
                if structure.get('method'):
                    analysis['methods'].add(structure['method'])
                if structure.get('sequence'):
                    analysis['sequences'].append({
                        'pdb_id': structure['pdb_id'],
                        'sequence': structure['sequence'],
                        'length': structure['sequence_length']
                    })
                analysis['ligands'].update(structure.get('ligands', []))

                if structure.get('resolution_A', 0) > 0:
                    analysis['quality_metrics'].append({
                        'pdb_id': structure['pdb_id'],
                        'resolution': structure['resolution_A'],
                        'r_work': structure.get('r_work', 0),
                        'r_free': structure.get('r_free', 0)
                    })

    # Convert sets to lists for JSON serialization
    analysis['total_structures'] = list(analysis['total_structures'])
    analysis['organisms'] = list(analysis['organisms'])
    analysis['methods'] = list(analysis['methods'])
    analysis['ligands'] = list(analysis['ligands'])

    return analysis

# Usage examples

# Combined search (web + protein)
combined_results = enhanced_combined_search("human insulin receptor kinase domain")
if combined_results:
    print("=== COMBINED SEARCH RESULTS ===")
    print(f"Found {len(combined_results['total_structures'])} unique structures")
    print(f"Organisms: {', '.join(combined_results['organisms'])}")
    print(f"Methods: {', '.join(combined_results['methods'])}")
    print(f"Sequences retrieved: {len(combined_results['sequences'])}")
    print(f"Quality structures: {len(combined_results['quality_metrics'])}")

# Web-only search
web_results = web_only_search("CRISPR Cas9 off-target effects")
if web_results:
    print("\n=== WEB SEARCH RESULTS ===")
    print(f"Query: {web_results['query']}")
    print(f"Papers found: {web_results['papers_found']}")
    print(f"Execution time: {web_results['execution_time']:.2f}s")
    print("Research papers:")
    for i, paper in enumerate(web_results['papers'][:3], 1):
        print(f"  {i}. {paper['title']}")
        print(f"     URL: {paper['url']}")
    print(f"Follow-up queries: {', '.join(web_results['follow_up_queries'])}")

# Protein-only search
protein_results = protein_only_search("crystallographic structures of DNA polymerase")
if protein_results:
    print("\n=== PROTEIN SEARCH RESULTS ===")
    print(f"Query: {protein_results['query']}")
    print(f"Tools used: {protein_results['total_tools_used']}")
    print(f"Successful tools: {protein_results['successful_tools']}")
    print(f"Unique structures: {len(protein_results['total_structures'])}")
    print(f"Organisms: {', '.join(protein_results['organisms'][:5])}...")
    print("Tool breakdown:")
    for tool_name, tool_info in protein_results['tool_breakdown'].items():
        if tool_info['success']:
            print(f"  ✅ {tool_name}: {tool_info['structures_found']} structures ({tool_info['execution_time']:.2f}s)")
        else:
            print(f"  ❌ {tool_name}: {tool_info['error']}")
```

---

## Running the Service

### Prerequisites

```bash
pip install fastapi uvicorn requests python-dotenv openai pydantic
```

### Environment Setup

Create `.env` file:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### Start Server

**Development:**

```bash
cd foldsearch
python main.py
```

**Production:**

```bash
cd foldsearch
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Testing Enhanced Features

```bash
# Test combined search (web + protein)
curl -X POST "http://127.0.0.1:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find structures similar to 1XDN containing ATP and analyze binding sites with high resolution data",
    "include_web": true,
    "include_protein": true,
    "max_protein_queries": 6
  }' \
  -o combined_search_test.json

# Test web-only search
curl -X POST "http://127.0.0.1:8000/web-search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "CRISPR Cas9 high-fidelity variants and off-target reduction strategies"
  }' \
  -o web_search_test.json

# Test protein-only search
curl -X POST "http://127.0.0.1:8000/protein-search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "human insulin receptor tyrosine kinase domain crystal structures"
  }' \
  -o protein_search_test.json

# View formatted results
echo "=== Combined Search Results ==="
jq '.data.tool_results | keys' combined_search_test.json
echo "=== Web Search Results ==="
jq '.data.research_paper.search_result | length' web_search_test.json
echo "=== Protein Search Results ==="
jq '.data.tool_results | length' protein_search_test.json

# Test health endpoint
curl -X GET "http://127.0.0.1:8000/health"

# View API information
curl -X GET "http://127.0.0.1:8000/"
```

---

## Performance Characteristics

### Enhanced Performance Features

- **Comprehensive Data Fetching**: 45-90 seconds for full enhanced search
- **Parallel Tool Execution**: Up to 10 protein tools run simultaneously
- **Auto-Enhancement**: Automatic fetching of structure details, sequences, and metadata
- **Tool-Specific Results**: No data loss between tools
- **Rich Metadata**: Quality metrics, statistics, and analysis included
- **Error Resilience**: Partial results with comprehensive fallback data

### Data Completeness Guarantee

✅ **No Null Values**: All fields populated with meaningful data  
✅ **Comprehensive Structures**: Title, method, resolution, organisms, sequences  
✅ **Quality Metrics**: R-factors, resolution statistics, quality scores  
✅ **Biological Context**: Organism information, entity details, assembly data  
✅ **Chemical Information**: Ligand binding, chemical properties, interaction sites  
✅ **Research Context**: Publication dates, research applications, functional classification

---

## Key Features Summary

🎯 **Tool-Specific Results**: Each tool maintains separate, comprehensive results  
📊 **Rich Metadata**: Extensive quality metrics and statistical analysis  
🧬 **Complete Sequences**: Full protein sequences with organism and type information  
🔬 **Detailed Structures**: Comprehensive experimental and quality data  
⚗️ **Chemical Analysis**: Ligand binding sites and chemical property analysis  
📈 **Statistical Insights**: Distribution analysis and trend identification  
🚀 **High Performance**: Parallel execution with comprehensive data fetching  
🛡️ **Error Resilience**: Graceful handling with meaningful fallback data

The enhanced FoldSearch API now provides unprecedented depth of structural biology data with guaranteed completeness and tool-specific organization for maximum research utility!
