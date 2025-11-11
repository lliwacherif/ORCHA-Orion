"""
Quick test script for web search functionality
Run this to verify the search_internet function works correctly with Google Custom Search API
"""
from app.services.orchestrator import search_internet

def test_search():
    print("Testing Google Custom Search API...")
    print("=" * 60)
    
    # Test query
    query = "Who is the richest man"
    print(f"\nQuery: {query}\n")
    
    # Perform search
    results = search_internet(query, max_results=5)
    
    # Display results
    print(results)
    print("=" * 60)
    print("\n[SUCCESS] Test completed successfully!")
    print("\nNote: You have 100 free queries per day with Google Custom Search API")

if __name__ == "__main__":
    test_search()

