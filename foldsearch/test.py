from agents.protein_search.worker import ProteinSearchAgent
from agents.web_search.worker import WebResearchAgent


if __name__ == "__main__":
    # Create the agent
    protein_search_agent = ProteinSearchAgent()
    web_search_agent = WebResearchAgent()

    research_query = """
    I'm investigating potential therapeutic applications of engineered Cas9 variants with enhanced specificity. I need comprehensive information about recent structural studies of high-fidelity Cas9 mutants, particularly focusing on the R661A/Q695A/Q926A variant that showed promising results in my preliminary experiments. I'm especially interested in understanding how these mutations affect the protein-DNA binding interface and recognition mechanism.

    Could you help me find detailed structural data, including crystal structures and molecular dynamics studies, that elucidate the conformational changes in modified Cas9 proteins? I'm particularly interested in structures showing the PAM-distal region interactions and any available protein-sgRNA-DNA ternary complexes. Additionally, any recent papers discussing novel protein engineering approaches to reduce off-target activity would be valuable for my research.
    """

    result = web_search_agent.search(research_query)
    research_papers = result.research_paper
    upnext_queries = result.upnext_queries

    print("\nSearch Results:")
    print(f"Number of follow-up queries generated: {len(result.upnext_queries)}")
    print("\nResearch paper results:")
    for item in result.research_paper.search_result:
        print(f"\nTitle: {item.title}")
        print(f"URL: {item.url}")
        print(f"Abstract: {item.abstract}")
        print("-" * 40)
    
    # Run tests
    for query in upnext_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: {query}")
        print('='*60)
        
        result = protein_search_agent.search(query)
        
        print(f"\nResult summary:")
        print(f"Success: {result.success}")
        print(f"Tool used: {result.tool_used}")
        print(f"PDB IDs found: {result.total_count}")
        if result.pdb_ids:
            print(f"Sample PDB IDs: {result.pdb_ids[:5]}")
        if result.error_message:
            print(f"Error: {result.error_message}")

