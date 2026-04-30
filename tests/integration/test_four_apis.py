#!/usr/bin/env python3
"""
Test script to test the four selected paper APIs integration.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.orchestrator import AcademicPaperOrchestrator
from src.utils.config_manager import ConfigManager


def test_four_apis():
    """Test the four selected paper APIs integration."""
    print("Testing the four selected paper APIs integration...")

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Create orchestrator
    orchestrator = AcademicPaperOrchestrator(config)

    # Test API connection
    print("\nTesting API connections...")
    connection_status = orchestrator.check_api_connection()
    for api_name, status in connection_status.items():
        if api_name in ["semantic_scholar", "arxiv", "pubmed", "openalex"]:
            if status.get("connected"):
                print(f"{api_name}: Connected ({status.get('response_time', 0):.2f}s)")
            else:
                print(f"{api_name}: Disconnected - {status.get('message', 'Unknown error')}")

    # Test search functionality
    test_queries = ["quantum computing", "machine learning", "artificial intelligence"]

    for query in test_queries:
        print(f"\nTesting search for: {query}")
        try:
            result = orchestrator.process_query(query, limit=5)
            print(f"Found {len(result.search_result.papers)} papers")
            if result.search_result.papers:
                print("First paper:")
                paper = result.search_result.papers[0]
                print(f"Title: {paper.title}")
                print(f"Authors: {[a.name for a in paper.authors]}")
                print(f"Year: {paper.year}")
                print(f"Venue: {paper.venue}")
                if paper.abstract:
                    print(f"Abstract: {paper.abstract[:100]}...")
            if result.llm_response.error:
                print(f"LLM Error: {result.llm_response.error}")
            else:
                print("LLM response generated successfully")
        except Exception as e:
            print(f"Error processing query: {e}")

    print("\nTest completed.")


if __name__ == "__main__":
    test_four_apis()
