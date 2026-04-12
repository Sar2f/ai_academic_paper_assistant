#!/usr/bin/env python3
"""
Test script to test the search functionality with arXiv fallback.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.orchestrator import AcademicPaperOrchestrator
from src.utils.config import AppConfig


def test_search():
    """Test search functionality with arXiv fallback."""
    print("Testing search functionality...")

    # Create config without API keys
    config = AppConfig(
        openai_api_key=None,
        anthropic_api_key=None,
        semantic_scholar_api_key=None,
        max_papers_to_retrieve=5,
        llm_model="gpt-4o-mini",
    )

    # Create orchestrator
    orchestrator = AcademicPaperOrchestrator(config)

    # Test search
    test_queries = ["quantum computing", "machine learning", "artificial intelligence"]

    for query in test_queries:
        print(f"\nSearching for: {query}")
        try:
            result = orchestrator.process_query(query)
            print(f"Found {len(result.search_result.papers)} papers")

            if result.search_result.papers:
                print("First paper:")
                paper = result.search_result.papers[0]
                print(f"Title: {paper.title}")
                print(f"Authors: {[a.name for a in paper.authors]}")
                print(f"Year: {paper.year}")

            if result.error:
                print(f"Error: {result.error}")
        except Exception as e:
            print(f"Error processing query: {e}")

    print("\nTest completed.")


if __name__ == "__main__":
    test_search()
