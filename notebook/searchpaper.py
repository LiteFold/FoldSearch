import requests
from typing import Dict, List, Optional, Literal
from datetime import datetime, timedelta
import time

# ===== CONSTANTS =====
BASE_URL = "https://api.biorxiv.org"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3

# ===== UTILITY FUNCTIONS =====

def _make_request(url: str, timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """Make HTTP request with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                
    return None

def _format_date(days_back: int) -> str:
    """Convert days back to yyyy-mm-dd format"""
    date = datetime.now() - timedelta(days=days_back)
    return date.strftime("%Y-%m-%d")

def _parse_paper(paper: Dict) -> Dict:
    """Parse paper data to extract useful information"""
    return {
        "title": paper.get("title", "").strip(),
        "authors": paper.get("authors", "").strip(),
        "abstract": paper.get("abstract", "").strip(),
        "doi": paper.get("doi", ""),
        "url": f"https://doi.org/{paper.get('doi', '')}" if paper.get("doi") else "",
        "date": paper.get("date", ""),
        "version": paper.get("version", 1),
        "category": paper.get("category", ""),
        "server": paper.get("server", ""),
        "published": paper.get("published", "NA")  # "Y" if published in journal, "NA" if not
    }

def _search_papers(server: Literal["biorxiv", "medrxiv"], start_date: str, 
                  end_date: str, query: str = None, limit: int = 100,
                  timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> List[Dict]:
    """Search papers within date range with optional text filtering"""
    cursor = 0
    matched = []
    
    while len(matched) < limit:
        url = f"{BASE_URL}/details/{server}/{start_date}/{end_date}/{cursor}/json"
        response = _make_request(url, timeout, max_retries)
        
        if not response:
            break
            
        # Check for API errors
        messages = response.get("messages", [])
        if messages:
            print(f"API Messages: {messages}")
            if any("error" in str(msg).lower() for msg in messages):
                break
        
        papers = response.get("collection", [])
        if not papers:
            break
        
        for paper in papers:
            # If query specified, filter by title/abstract
            if query:
                title = paper.get("title", "").lower()
                abstract = paper.get("abstract", "").lower()
                query_lower = query.lower()
                
                if query_lower not in title and query_lower not in abstract:
                    continue
            
            matched.append(_parse_paper(paper))
            if len(matched) >= limit:
                break
        
        cursor += 100
        # Avoid hitting rate limits
        time.sleep(0.1)
    
    return matched[:limit]

# ===== MAIN SEARCH FUNCTIONS =====

def search_recent(query: str, server: Literal["biorxiv", "medrxiv"] = "biorxiv", 
                 days_back: int = 30, limit: int = 50, timeout: int = DEFAULT_TIMEOUT, 
                 max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search recent papers by query terms
    
    Args:
        query: Search terms to find in title/abstract
        server: "biorxiv" or "medrxiv"
        days_back: How many days back to search
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with papers list, search_info, and summary stats
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = _format_date(days_back)
    
    papers = _search_papers(server, start_date, end_date, query, limit, timeout, max_retries)
    
    return {
        "papers": papers,
        "search_info": {
            "query": query,
            "server": server,
            "date_range": f"{start_date} to {end_date}",
            "days_searched": days_back
        },
        "summary": {
            "found_count": len(papers),
            "published_count": sum(1 for p in papers if p["published"] == "Y"),
            "preprint_count": sum(1 for p in papers if p["published"] == "NA")
        }
    }

def search_by_date_range(start_date: str, end_date: str, 
                        server: Literal["biorxiv", "medrxiv"] = "biorxiv",
                        query: str = None, limit: int = 100, timeout: int = DEFAULT_TIMEOUT,
                        max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search papers in specific date range
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format  
        server: "biorxiv" or "medrxiv"
        query: Optional search terms (if None, returns all papers in range)
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with papers list, search_info, and summary stats
    """
    papers = _search_papers(server, start_date, end_date, query, limit, timeout, max_retries)
    
    return {
        "papers": papers,
        "search_info": {
            "query": query or "All papers",
            "server": server,
            "date_range": f"{start_date} to {end_date}"
        },
        "summary": {
            "found_count": len(papers),
            "published_count": sum(1 for p in papers if p["published"] == "Y"),
            "preprint_count": sum(1 for p in papers if p["published"] == "NA")
        }
    }

def search_both_servers(query: str, days_back: int = 30, limit: int = 50, 
                       timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search both bioRxiv and medRxiv simultaneously
    
    Args:
        query: Search terms to find in title/abstract
        days_back: How many days back to search
        limit: Maximum number of results per server
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with combined results from both servers
    """
    biorxiv_results = search_recent(query, "biorxiv", days_back, limit, timeout, max_retries)
    medrxiv_results = search_recent(query, "medrxiv", days_back, limit, timeout, max_retries)
    
    all_papers = biorxiv_results["papers"] + medrxiv_results["papers"]
    
    # Sort by date (most recent first)
    all_papers.sort(key=lambda x: x["date"], reverse=True)
    
    return {
        "papers": all_papers,
        "search_info": {
            "query": query,
            "servers": ["biorxiv", "medrxiv"],
            "days_searched": days_back
        },
        "summary": {
            "total_found": len(all_papers),
            "biorxiv_count": len(biorxiv_results["papers"]),
            "medrxiv_count": len(medrxiv_results["papers"]),
            "published_count": sum(1 for p in all_papers if p["published"] == "Y"),
            "preprint_count": sum(1 for p in all_papers if p["published"] == "NA")
        }
    }

# ===== SPECIALIZED SEARCHES =====

def search_ai_ml_papers(days_back: int = 30, limit: int = 50, timeout: int = DEFAULT_TIMEOUT,
                       max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for AI/ML related papers
    
    Args:
        days_back: How many days back to search
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with AI/ML papers from both servers
    """
    ai_terms = [
        "artificial intelligence", "machine learning", "deep learning", 
        "neural network", "transformer", "alphafold", "AI", "ML"
    ]
    
    all_papers = []
    for term in ai_terms[:3]:  # Search top 3 terms to avoid too many requests
        results = search_both_servers(term, days_back, limit//3, timeout, max_retries)
        all_papers.extend(results["papers"])
    
    # Remove duplicates by DOI
    seen_dois = set()
    unique_papers = []
    for paper in all_papers:
        if paper["doi"] and paper["doi"] not in seen_dois:
            seen_dois.add(paper["doi"])
            unique_papers.append(paper)
    
    # Sort by date
    unique_papers.sort(key=lambda x: x["date"], reverse=True)
    
    return {
        "papers": unique_papers[:limit],
        "search_info": {
            "query": "AI/ML related terms",
            "terms_searched": ai_terms[:3],
            "days_searched": days_back
        },
        "summary": {
            "found_count": len(unique_papers[:limit]),
            "published_count": sum(1 for p in unique_papers[:limit] if p["published"] == "Y"),
            "preprint_count": sum(1 for p in unique_papers[:limit] if p["published"] == "NA")
        }
    }

def search_structural_biology(days_back: int = 30, limit: int = 50, timeout: int = DEFAULT_TIMEOUT,
                             max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Search for structural biology papers
    
    Args:
        days_back: How many days back to search
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with structural biology papers
    """
    struct_terms = [
        "crystal structure", "protein structure", "cryo-EM", "NMR", 
        "X-ray crystallography", "structural biology"
    ]
    
    all_papers = []
    for term in struct_terms[:3]:
        results = search_both_servers(term, days_back, limit//3, timeout, max_retries)
        all_papers.extend(results["papers"])
    
    # Remove duplicates and sort
    seen_dois = set()
    unique_papers = []
    for paper in all_papers:
        if paper["doi"] and paper["doi"] not in seen_dois:
            seen_dois.add(paper["doi"])
            unique_papers.append(paper)
    
    unique_papers.sort(key=lambda x: x["date"], reverse=True)
    
    return {
        "papers": unique_papers[:limit],
        "search_info": {
            "query": "Structural biology terms",
            "terms_searched": struct_terms[:3],
            "days_searched": days_back
        },
        "summary": {
            "found_count": len(unique_papers[:limit]),
            "published_count": sum(1 for p in unique_papers[:limit] if p["published"] == "Y"),
            "preprint_count": sum(1 for p in unique_papers[:limit] if p["published"] == "NA")
        }
    }

# ===== UTILITY FUNCTIONS =====

def get_paper_details(doi: str, server: Literal["biorxiv", "medrxiv"] = "biorxiv",
                     timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES) -> Optional[Dict]:
    """
    Get detailed information for a specific paper by DOI
    
    Args:
        doi: DOI of the paper
        server: Which server to search
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary with paper details or None if not found
    """
    url = f"{BASE_URL}/details/{server}/{doi}/json"
    response = _make_request(url, timeout, max_retries)
    
    if response and response.get("collection"):
        paper = response["collection"][0]
        return _parse_paper(paper)
    
    return None

def get_latest_papers(server: Literal["biorxiv", "medrxiv"] = "biorxiv", 
                     days: int = 1, limit: int = 20, timeout: int = DEFAULT_TIMEOUT,
                     max_retries: int = DEFAULT_MAX_RETRIES) -> Dict:
    """
    Get the latest papers from the last few days without filtering
    
    Args:
        server: "biorxiv" or "medrxiv"
        days: Number of recent days
        limit: Maximum number of results
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict with latest papers
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = _format_date(days)
    
    papers = _search_papers(server, start_date, end_date, query=None, limit=limit, timeout=timeout, max_retries=max_retries)
    
    return {
        "papers": papers,
        "search_info": {
            "server": server,
            "date_range": f"{start_date} to {end_date}",
            "days": days
        },
        "summary": {
            "found_count": len(papers),
            "published_count": sum(1 for p in papers if p["published"] == "Y"),
            "preprint_count": sum(1 for p in papers if p["published"] == "NA")
        }
    }

# ===== EXAMPLE USAGE =====
if __name__ == "__main__":
    # Search for protein folding papers
    results = search_recent("protein folding", days_back=30, limit=5)
    
    print(f"Found {results['summary']['found_count']} protein folding papers")
    print(f"Search period: {results['search_info']['date_range']}\n")
    
    for i, paper in enumerate(results["papers"], 1):
        print(f"{i}. {paper['title']}")
        print(f"   Authors: {paper['authors']}")
        print(f"   Date: {paper['date']} | DOI: {paper['doi']}")
        print(f"   Published: {paper['published']}")
        print(f"   Abstract: {paper['abstract'][:150]}...")
        print(f"   URL: {paper['url']}\n")