#!/usr/bin/env python3
"""
Test script for the FoldSearch API
Run this to test the API endpoints
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running.")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print("🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Root endpoint working")
            print(f"   API Version: {data.get('version')}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_search_endpoint():
    """Test the main search endpoint"""
    print("🔍 Testing search endpoint...")
    
    # Test query
    test_query = """
    Find information about high-fidelity Cas9 variants with enhanced specificity, 
    particularly focusing on structural studies of R661A/Q695A/Q926A mutations.
    """
    
    search_request = {
        "query": test_query.strip(),
        "include_web": True,
        "include_protein": True,
        "max_protein_queries": 3
    }
    
    print(f"   Query: {search_request['query'][:100]}...")
    print(f"   Include web: {search_request['include_web']}")
    print(f"   Include protein: {search_request['include_protein']}")
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/search", json=search_request, timeout=300)  # 5 minute timeout
        execution_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Search endpoint working")
            print(f"   Success: {data.get('success')}")
            print(f"   Execution time: {execution_time:.2f}s")
            print(f"   Message: {data.get('message')}")
            
            # Check if we have results
            if data.get('data'):
                result_data = data['data']
                print(f"   Search type: {result_data.get('search_type')}")
                
                # Web results
                if result_data.get('web_research'):
                    web_results = result_data['web_research']['research_paper']['search_result']
                    print(f"   Web results: {len(web_results)} papers found")
                    
                # Protein results
                if result_data.get('protein_search'):
                    protein_data = result_data['protein_search']
                    pdb_count = protein_data.get('total_count', 0)
                    print(f"   Protein results: {pdb_count} PDB IDs found")
                    if protein_data.get('pdb_ids'):
                        sample_pdbs = protein_data['pdb_ids'][:5]
                        print(f"   Sample PDB IDs: {sample_pdbs}")
            
            return True
        else:
            print(f"❌ Search endpoint failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Search request timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Search endpoint error: {e}")
        return False

def test_search_web_only():
    """Test search with web results only"""
    print("🔍 Testing web-only search...")
    
    search_request = {
        "query": "CRISPR Cas9 high fidelity variants",
        "include_web": True,
        "include_protein": False,
        "max_protein_queries": 0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/search", json=search_request, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Web-only search working")
            result_data = data.get('data', {})
            print(f"   Search type: {result_data.get('search_type')}")
            return True
        else:
            print(f"❌ Web-only search failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Web-only search error: {e}")
        return False

def test_search_protein_only():
    """Test search with protein results only"""
    print("🔍 Testing protein-only search...")
    
    search_request = {
        "query": "Cas9 crystal structures",
        "include_web": False,
        "include_protein": True,
        "max_protein_queries": 1
    }
    
    try:
        response = requests.post(f"{BASE_URL}/search", json=search_request, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Protein-only search working")
            result_data = data.get('data', {})
            print(f"   Search type: {result_data.get('search_type')}")
            return True
        else:
            print(f"❌ Protein-only search failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Protein-only search error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting FoldSearch API Tests")
    print("=" * 50)
    
    tests = [
        test_health_endpoint,
        test_root_endpoint,
        test_search_web_only,
        test_search_protein_only,
        test_search_endpoint,  # Full test last as it takes longest
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()  # Add spacing between tests
        except KeyboardInterrupt:
            print("\n⚠️  Tests interrupted by user")
            break
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    exit(main()) 