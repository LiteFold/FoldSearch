"""
ChEMBL Search API Demo

Examples demonstrating how to use the ChEMBL search functions for drug discovery tasks.
"""

from chembl_search import (
    molecule_search, similarity_search, substructure_search, activity_search,
    target_search, drug_search, drug_like_molecules, get_molecule_properties,
    get_target_activities, get_chembl_stats
)

def demo_molecule_search():
    """Demo molecule search functionality."""
    print("=== Molecule Search Demo ===")
    
    # Search by name
    print("\n1. Search for aspirin by name:")
    results = molecule_search("aspirin", identifier_type="name", limit=5)
    if "error" not in results:
        print(f"Found {results['count']} molecules")
        for mol in results['results'][:2]:  # Show first 2
            print(f"- {mol['chembl_id']}: {mol['pref_name']} (MW: {mol['molecular_weight']})")
    
    # Search by ChEMBL ID
    print("\n2. Search by ChEMBL ID:")
    results = molecule_search("CHEMBL25", identifier_type="chembl_id")
    if "error" not in results and results['results']:
        mol = results['results'][0]
        print(f"Found: {mol['chembl_id']} - {mol['pref_name']}")
        print(f"SMILES: {mol['smiles']}")

def demo_similarity_search():
    """Demo similarity search functionality."""
    print("\n=== Similarity Search Demo ===")
    
    # Aspirin SMILES
    aspirin_smiles = "CC(=O)Oc1ccccc1C(=O)O"
    
    print(f"\nSearching for molecules similar to aspirin (≥70% similarity):")
    results = similarity_search(aspirin_smiles, similarity_threshold=70, limit=5)
    
    if "error" not in results:
        print(f"Found {results['count']} similar molecules")
        for mol in results['results'][:3]:  # Show first 3
            print(f"- {mol['chembl_id']}: {mol['pref_name']} "
                  f"(Similarity: {mol['similarity_score']}%, MW: {mol['molecular_weight']})")

def demo_activity_search():
    """Demo activity search functionality."""
    print("\n=== Activity Search Demo ===")
    
    # Search for IC50 activities of aspirin
    print("\n1. IC50 activities for aspirin (CHEMBL25):")
    results = activity_search(
        molecule_chembl_id="CHEMBL25", 
        activity_types=["IC50"], 
        limit=5
    )
    
    if "error" not in results:
        print(f"Found {results['count']} IC50 activities")
        for act in results['results'][:3]:  # Show first 3
            print(f"- Target: {act['target_chembl_id']}, "
                  f"IC50: {act['activity_value']} {act['activity_units']}")
    
    # Search for activities against a specific target
    print("\n2. Activities against hERG (CHEMBL240):")
    results = activity_search(
        target_chembl_id="CHEMBL240", 
        activity_types=["IC50", "Ki"], 
        limit=5
    )
    
    if "error" not in results:
        print(f"Found {results['count']} activities against hERG")
        for act in results['results'][:3]:  # Show first 3
            print(f"- Molecule: {act['molecule_chembl_id']}, "
                  f"{act['activity_type']}: {act['activity_value']} {act['activity_units']}")

def demo_target_search():
    """Demo target search functionality."""
    print("\n=== Target Search Demo ===")
    
    # Search by gene name
    print("\n1. Search for BRD4 targets:")
    results = target_search("BRD4", search_type="gene_name", limit=5)
    
    if "error" not in results:
        print(f"Found {results['count']} BRD4-related targets")
        for target in results['results'][:3]:  # Show first 3
            print(f"- {target['target_chembl_id']}: {target['pref_name']} "
                  f"({target['organism']})")
    
    # Search by target name
    print("\n2. Search for kinase targets:")
    results = target_search("kinase", search_type="name", limit=5)
    
    if "error" not in results:
        print(f"Found {results['count']} kinase targets")
        for target in results['results'][:2]:  # Show first 2
            print(f"- {target['target_chembl_id']}: {target['pref_name']}")

def demo_drug_search():
    """Demo drug search functionality."""
    print("\n=== Drug Search Demo ===")
    
    # Search for approved cancer drugs
    print("\n1. Approved cancer drugs:")
    results = drug_search(
        max_phase=4, 
        indication_class="cancer", 
        limit=5
    )
    
    if "error" not in results:
        print(f"Found {results['count']} approved cancer drugs")
        for drug in results['results'][:3]:  # Show first 3
            print(f"- {drug['chembl_id']}: {drug['pref_name']} "
                  f"(MW: {drug['molecular_weight']})")
    
    # Search for small molecule drugs
    print("\n2. Small molecule approved drugs (MW < 500):")
    results = drug_search(
        max_phase=4, 
        molecular_weight_max=500, 
        limit=5
    )
    
    if "error" not in results:
        print(f"Found {results['count']} small molecule drugs")
        for drug in results['results'][:3]:  # Show first 3
            print(f"- {drug['chembl_id']}: {drug['pref_name']} "
                  f"(MW: {drug['molecular_weight']})")

def demo_drug_like_search():
    """Demo drug-like molecule search."""
    print("\n=== Drug-like Molecules Demo ===")
    
    # Search for high-quality drug-like molecules
    print("\nHigh-quality drug-like molecules (0 RO5 violations, QED ≥ 0.7):")
    results = drug_like_molecules(ro5_violations=0, qed_min=0.7, limit=5)
    
    if "error" not in results:
        print(f"Found {results['count']} high-quality drug-like molecules")
        for mol in results['results'][:3]:  # Show first 3
            print(f"- {mol['chembl_id']}: {mol['pref_name']} "
                  f"(MW: {mol['molecular_weight']}, ALogP: {mol['alogp']})")

def demo_molecule_properties():
    """Demo detailed molecule properties."""
    print("\n=== Molecule Properties Demo ===")
    
    # Get detailed properties for aspirin
    print("\nDetailed properties for aspirin (CHEMBL25):")
    properties = get_molecule_properties("CHEMBL25")
    
    if "error" not in properties:
        print(f"Name: {properties['pref_name']}")
        print(f"SMILES: {properties['smiles']}")
        print(f"Molecular Weight: {properties['molecular_weight']}")
        print(f"LogP: {properties['alogp']}")
        print(f"HBD: {properties['hbd']}, HBA: {properties['hba']}")
        print(f"PSA: {properties['psa']}")
        print(f"QED: {properties['qed_weighted']}")
        print(f"RO5 Violations: {properties['ro5_violations']}")
        print(f"Max Phase: {properties['max_phase']}")
        print(f"Indication: {properties['indication_class']}")

def demo_substructure_search():
    """Demo substructure search."""
    print("\n=== Substructure Search Demo ===")
    
    # Search for benzene ring containing molecules
    benzene_smiles = "c1ccccc1"
    print(f"\nSearching for molecules containing benzene ring:")
    results = substructure_search(benzene_smiles, limit=5)
    
    if "error" not in results:
        print(f"Found {results['count']} molecules with benzene ring")
        for mol in results['results'][:3]:  # Show first 3
            print(f"- {mol['chembl_id']}: {mol['pref_name']} "
                  f"(MW: {mol['molecular_weight']})")

def main():
    """Run all demos."""
    print("ChEMBL Search API Demo")
    print("=" * 50)
    
    try:
        demo_molecule_search()
        demo_similarity_search()
        demo_activity_search()
        demo_target_search()
        demo_drug_search()
        demo_drug_like_search()
        demo_molecule_properties()
        demo_substructure_search()
        
        print("\n=== ChEMBL Database Stats ===")
        stats = get_chembl_stats()
        if "error" not in stats:
            print(f"Total compounds: {stats['total_compounds']:,}")
            print(f"Approved drugs: {stats['approved_drugs']:,}")
            print(f"Total targets: {stats['total_targets']:,}")
            print(f"Total activities: {stats['total_activities']:,}")
        
    except Exception as e:
        print(f"Demo failed with error: {str(e)}")
        print("Make sure you have chembl_webresource_client installed:")
        print("pip install chembl_webresource_client")

if __name__ == "__main__":
    main() 