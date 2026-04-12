#!/usr/bin/env python3
"""
Test script to check Semantic Scholar API connection.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.api.semantic_scholar import SemanticScholarAPI


def main():
    """Test Semantic Scholar API connection."""
    print("Testing Semantic Scholar API connection...")

    # Create API client without API key
    api = SemanticScholarAPI()

    # Test connection
    print("Checking connection...")
    connection_status = api.check_connection()
    print(f"Connection status: {connection_status}")

    # Test search
    print("\nTesting search...")
    search_result = api.search_papers("machine learning", limit=3)
    print(f"Search result: {search_result}")
    print(f"Found {len(search_result.papers)} papers")

    if search_result.papers:
        print("\nFirst paper:")
        paper = search_result.papers[0]
        print(f"Title: {paper.title}")
        print(f"Authors: {[a.name for a in paper.authors]}")
        print(f"Year: {paper.year}")
        print(f"Abstract: {paper.abstract[:100]}..." if paper.abstract else "Abstract: None")

    print("\nTest completed.")


if __name__ == "__main__":
    main()
