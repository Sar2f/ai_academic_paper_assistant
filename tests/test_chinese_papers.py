#!/usr/bin/env python3
"""
Test script to test searching for Chinese papers using arXiv API.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.api.arxiv_api import ArxivAPI


def test_chinese_search():
    """Test searching for Chinese papers using arXiv API."""
    print("Testing Chinese paper search...")

    # Create arXiv API client
    arxiv_api = ArxivAPI()

    # Test Chinese queries
    test_queries = ["量子计算", "机器学习", "人工智能", "深度学习"]

    for query in test_queries:
        print(f"\nSearching for: {query}")
        try:
            # Test with different search approaches
            # 1. Direct Chinese query
            result = arxiv_api.search_papers(query, limit=5)
            print(f"Direct search found {len(result.papers)} papers")

            if result.papers:
                print("First paper:")
                paper = result.papers[0]
                print(f"Title: {paper.title}")
                print(f"Authors: {[a.name for a in paper.authors]}")
                print(f"Year: {paper.year}")
        except Exception as e:
            print(f"Error searching: {e}")

    # Test with English translations
    print("\n\nTesting with English translations...")
    translation_map = {
        "量子计算": "quantum computing",
        "机器学习": "machine learning",
        "人工智能": "artificial intelligence",
        "深度学习": "deep learning"
    }

    for chinese_query, english_query in translation_map.items():
        print(f"\nSearching for '{chinese_query}' as '{english_query}'")
        try:
            result = arxiv_api.search_papers(english_query, limit=5)
            print(f"Found {len(result.papers)} papers")

            if result.papers:
                print("First paper:")
                paper = result.papers[0]
                print(f"Title: {paper.title}")
                print(f"Authors: {[a.name for a in paper.authors]}")
                print(f"Year: {paper.year}")
        except Exception as e:
            print(f"Error searching: {e}")

    print("\nTest completed.")


if __name__ == "__main__":
    test_chinese_search()
