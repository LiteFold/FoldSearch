# FoldSearch API

A FastAPI-based web service that combines web research and protein structure search capabilities.

## Features

- **Combined Search**: Integrates web research and protein structure search in a single API call
- **De-duplication**: Automatically removes duplicate PDB IDs and other protein search results
- **Parallel Processing**: Runs multiple searches concurrently for optimal performance
- **Flexible Configuration**: Choose to include/exclude web or protein search results
- **Comprehensive Results**: Returns unified results with metadata and execution statistics

## Installation

1. Make sure you have the required dependencies:

```bash
pip install fastapi uvicorn requests python-dotenv openai pydantic
```

2. Set up your environment variables (create a `.env` file):

```
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the Server

### Development Mode

```bash
cd foldsearch
python main.py
```

### Production Mode

```bash
cd foldsearch
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`

## API Endpoints

### `POST /search`

Main search endpoint that combines web research and protein structure search.

**Request Body:**

```json
{
  "query": "Find information about high-fidelity Cas9 variants",
  "include_web": true,
  "include_protein": true,
  "max_protein_queries": 5
}
```

**Parameters:**

- `query` (string, required): The search query
- `include_web` (boolean, optional, default: true): Include web research results
- `include_protein` (boolean, optional, default: true): Include protein structure search results
- `max_protein_queries` (integer, optional, default: 5): Maximum number of follow-up protein queries to run

## TypeScript Interfaces

```typescript
// Request interface
interface SearchRequest {
  query: string;
  include_web?: boolean;
  include_protein?: boolean;
  max_protein_queries?: number;
}

// Research paper interface
interface ResearchPaper {
  title: string;
  url: string;
  abstract: string;
}

// Web research interface
interface WebResearch {
  query: string;
  raw_result: string;
  research_paper: {
    search_result: ResearchPaper[];
  };
  upnext_queries: string[];
}

// Protein search interface
interface ProteinSearch {
  operation_type: string;
  tool_used: string;
  query_params: {
    combined_queries: number;
  };
  execution_time: number;
  timestamp: string;
  success: boolean;
  error_message?: string;
  warnings?: string;
  pdb_ids: string[];
  total_count: number;
  returned_count: number;
  scores: Record<string, number>;
  raw_response: {
    original_results_count: number;
    deduplicated_pdb_count: number;
    individual_counts: number[];
  };
  successful_retrievals: number;
  failed_retrievals: number;
  // Additional optional fields that may be present
  by_reference?: any;
  structure_details?: any;
  pdb_id?: string;
  title?: string;
  method?: string;
  resolution_A?: number;
  r_work?: number;
  r_free?: number;
  space_group?: string;
  polymer_entity_count?: number;
  ligands?: any;
  deposition_date?: string;
  entities?: any;
  assembly?: any;
  oligomeric_state?: string;
  oligomeric_count?: number;
  assembly_method?: string;
  quality_score?: number;
  protein_entities?: any;
  total_entities?: number;
  ligand_count?: number;
  unique_organisms?: any;
  organisms?: any;
  has_ligands?: boolean;
  is_complex?: boolean;
  high_resolution?: boolean;
  sequences?: any;
  entity_id?: string;
  sequence?: string;
  sequence_length?: number;
  sequence_type?: string;
  molecule_type?: string;
  comparisons?: any;
  comparison_summary?: string;
  sequence_identity?: number;
  length_difference?: number;
  structural_similarity?: number;
  comparison_note?: string;
  interactions?: any;
  protein_chains?: any;
  interaction_types?: any;
  interaction_descriptions?: any;
  quaternary_structure?: any;
  multi_chain_complex?: boolean;
  chain_count?: number;
  protein_ligand_interactions?: any;
  bound_ligands?: any;
  experimental_method?: string;
  experimental_details?: any;
  organism?: string;
  scientific_name?: string;
  common_name?: string;
  taxonomy_id?: number;
  smiles?: string;
  inchi?: string;
  ligand_name?: string;
  chemical_identifier?: string;
  search_query?: string;
  search_organism?: string;
  search_method?: string;
  max_resolution?: number;
  identity_cutoff?: number;
  evalue_cutoff?: number;
  reference_pdb_ids?: string[];
  assembly_id?: string;
  match_type?: string;
  max_r_work?: number;
  max_r_free?: number;
  min_year?: number;
  limit?: number;
  start_index?: number;
  raw_query?: string;
  total_structures?: number;
  multiple_structures?: any;
  structure_count?: number;
  notes?: string;
  additional_info?: any;
}

// Main search data interface
interface SearchData {
  query: string;
  web_research?: WebResearch;
  protein_search?: ProteinSearch;
  search_type: "combined" | "web" | "protein" | "none";
  timestamp: string;
  success: boolean;
  error_message?: string;
}

// Main API response interface
interface SearchResponse {
  success: boolean;
  message: string;
  data: SearchData;
  execution_time: number;
  timestamp: string;
}

// Health check response
interface HealthResponse {
  status: "healthy" | "unhealthy";
  timestamp: string;
}

// Root endpoint response
interface RootResponse {
  message: string;
  version: string;
  endpoints: {
    search: string;
    health: string;
    docs: string;
  };
}
```

## Response Format

### Successful Search Response

```json
{
  "success": true,
  "message": "Search completed successfully. 6 web results; Protein: combined_protein_search completed with 100 results",
  "data": {
    "query": "Your search query here",
    "web_research": {
      "query": "Your search query here",
      "raw_result": "Detailed research findings as text...",
      "research_paper": {
        "search_result": [
          {
            "title": "Paper Title",
            "url": "https://example.com/paper",
            "abstract": "Paper abstract content..."
          }
        ]
      },
      "upnext_queries": ["Follow-up query 1", "Follow-up query 2"]
    },
    "protein_search": {
      "operation_type": "combined_protein_search",
      "tool_used": "get_high_quality_structures_tool, search_structures_tool, analyze_interactions_tool",
      "query_params": {
        "combined_queries": 5
      },
      "execution_time": 0.005127,
      "timestamp": "2025-06-21T23:27:15.307884",
      "success": true,
      "error_message": null,
      "warnings": null,
      "pdb_ids": ["1ABC", "2DEF", "3GHI"],
      "total_count": 100,
      "returned_count": 100,
      "scores": {
        "1ABC": 1.0,
        "2DEF": 0.95,
        "3GHI": 0.9
      },
      "raw_response": {
        "original_results_count": 5,
        "deduplicated_pdb_count": 100,
        "individual_counts": [50, 100, 50, 2, 1]
      },
      "successful_retrievals": 5,
      "failed_retrievals": 0
    },
    "search_type": "combined",
    "timestamp": "2025-06-21T23:27:15.309106",
    "success": true,
    "error_message": null
  },
  "execution_time": 44.15591,
  "timestamp": "2025-06-21T23:27:15.309230"
}
```

### Error Response

```json
{
  "success": false,
  "message": "Error description",
  "data": {
    "query": "Your search query here",
    "search_type": "none",
    "timestamp": "2025-06-21T23:27:15.309106",
    "success": false,
    "error_message": "Detailed error message"
  },
  "execution_time": 5.23,
  "timestamp": "2025-06-21T23:27:15.309230"
}
```

### `GET /health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### `GET /`

Root endpoint with API information.

**Response:**

```json
{
  "message": "FoldSearch API",
  "version": "1.0.0",
  "endpoints": {
    "search": "/search - Main search endpoint (POST)",
    "health": "/health - Health check (GET)",
    "docs": "/docs - API documentation (GET)"
  }
}
```

### `GET /docs`

Interactive API documentation (Swagger UI).

## Frontend Integration Examples

### React/TypeScript Example

```typescript
import { useState } from "react";

const API_BASE_URL = "http://localhost:8000";

interface SearchHook {
  searchData: SearchResponse | null;
  loading: boolean;
  error: string | null;
  search: (request: SearchRequest) => Promise<void>;
}

export const useSearch = (): SearchHook => {
  const [searchData, setSearchData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = async (request: SearchRequest) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SearchResponse = await response.json();
      setSearchData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return { searchData, loading, error, search };
};

// Usage in component
const SearchComponent = () => {
  const { searchData, loading, error, search } = useSearch();

  const handleSearch = () => {
    search({
      query: "CRISPR Cas9 high fidelity variants",
      include_web: true,
      include_protein: true,
      max_protein_queries: 5,
    });
  };

  return (
    <div>
      <button onClick={handleSearch} disabled={loading}>
        {loading ? "Searching..." : "Search"}
      </button>

      {error && <div className="error">Error: {error}</div>}

      {searchData && (
        <div>
          <h3>Search Results</h3>
          <p>Execution time: {searchData.execution_time}s</p>
          <p>Message: {searchData.message}</p>

          {searchData.data.web_research && (
            <div>
              <h4>
                Research Papers (
                {
                  searchData.data.web_research.research_paper.search_result
                    .length
                }
                )
              </h4>
              {searchData.data.web_research.research_paper.search_result.map(
                (paper, index) => (
                  <div key={index}>
                    <h5>{paper.title}</h5>
                    <p>{paper.abstract}</p>
                    <a
                      href={paper.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Read more
                    </a>
                  </div>
                )
              )}
            </div>
          )}

          {searchData.data.protein_search && (
            <div>
              <h4>
                Protein Structures (
                {searchData.data.protein_search.pdb_ids.length})
              </h4>
              <p>
                Total structures found:{" "}
                {searchData.data.protein_search.total_count}
              </p>
              <div>
                {searchData.data.protein_search.pdb_ids
                  .slice(0, 10)
                  .map((pdbId) => (
                    <span key={pdbId} className="pdb-id">
                      {pdbId}
                    </span>
                  ))}
                {searchData.data.protein_search.pdb_ids.length > 10 && (
                  <span>
                    ... and {searchData.data.protein_search.pdb_ids.length - 10}{" "}
                    more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

### Axios Example

```typescript
import axios, { AxiosResponse } from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export const searchAPI = {
  search: async (request: SearchRequest): Promise<SearchResponse> => {
    const response: AxiosResponse<SearchResponse> = await api.post(
      "/search",
      request
    );
    return response.data;
  },

  health: async (): Promise<HealthResponse> => {
    const response: AxiosResponse<HealthResponse> = await api.get("/health");
    return response.data;
  },

  root: async (): Promise<RootResponse> => {
    const response: AxiosResponse<RootResponse> = await api.get("/");
    return response.data;
  },
};
```

## Testing

Run the test script to verify the API is working correctly:

```bash
cd foldsearch
python test_api.py
```

Make sure the server is running before running the tests.

## Key Features Explained

### De-duplication

When multiple protein searches are performed (based on follow-up queries from web research), the API automatically:

- Removes duplicate PDB IDs using set operations
- Merges scores and metadata from all searches
- Provides statistics on original vs. deduplicated results

### Parallel Processing

The API runs searches in parallel for optimal performance:

- Web search runs first to generate follow-up queries
- Multiple protein searches run concurrently based on follow-up queries
- Results are aggregated and returned as a unified response

### Error Handling

- Individual search failures don't stop the entire process
- Partial results are returned when possible
- Detailed error messages help with debugging
- The `success` field in both the main response and nested data indicates operation status

### Search Types

The API automatically determines the search type based on results:

- `"combined"`: Both web and protein results available
- `"web"`: Only web results available
- `"protein"`: Only protein results available
- `"none"`: No results found

## Response Fields Explanation

### Main Response Fields

- `success`: Boolean indicating if the overall operation succeeded
- `message`: Human-readable description of the operation result
- `data`: Main search results and metadata
- `execution_time`: Total time taken for the search in seconds
- `timestamp`: ISO timestamp of when the response was generated

### Data Fields

- `query`: The original search query
- `web_research`: Web search results (present if `include_web` is true)
- `protein_search`: Protein structure search results (present if `include_protein` is true)
- `search_type`: Type of search performed based on available results
- `timestamp`: When the search data was generated
- `success`: Whether the search operation succeeded
- `error_message`: Error details if the search failed

### Protein Search Fields

- `pdb_ids`: Array of PDB structure identifiers found
- `total_count`: Total number of structures found
- `returned_count`: Number of structures returned (may be limited)
- `scores`: Relevance scores for each PDB ID (higher is better)
- `execution_time`: Time taken for protein search in seconds
- `successful_retrievals`: Number of successful search operations
- `failed_retrievals`: Number of failed search operations

## Example Usage

### Python Client

```python
import requests

# Basic search
response = requests.post("http://localhost:8000/search", json={
    "query": "CRISPR Cas9 high fidelity variants"
})

data = response.json()
if data['success']:
    print(f"Found {len(data['data']['protein_search']['pdb_ids'])} PDB structures")
    print(f"Execution time: {data['execution_time']}s")
else:
    print(f"Search failed: {data['message']}")
```

### cURL

```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "CRISPR Cas9 high fidelity variants",
       "include_web": true,
       "include_protein": true,
       "max_protein_queries": 3
     }'
```

## Architecture

The API consists of:

1. **Web Research Agent**: Uses OpenAI's search capabilities to find research papers
2. **Protein Search Agent**: Searches protein databases using multiple specialized tools
3. **Aggregation Layer**: Combines and deduplicates results from both agents
4. **FastAPI Server**: Provides REST API interface with async support

## Performance Notes

- Full combined searches typically take 30-60 seconds
- Web-only searches are faster (10-20 seconds)
- Protein-only searches vary based on query complexity (5-30 seconds)
- Results are cached within the request lifecycle for efficiency
- The API handles timeouts gracefully and returns partial results when possible
