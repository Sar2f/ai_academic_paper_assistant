#!/usr/bin/env python3
"""
Test script to check orchestrator functionality without API keys.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.orchestrator import AcademicPaperOrchestrator
from src.utils.config import AppConfig


def main():
    """Test orchestrator functionality."""
    print("Testing orchestrator functionality...")

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

    # Test API connection
    print("Checking API connections...")
    connection_status = orchestrator.check_api_connection()
    print(f"Semantic Scholar status: {connection_status['semantic_scholar']}")

    # Test search
    print("\nTesting search...")
    try:
        result = orchestrator.process_query("machine learning")
        print(f"Processing result: {result}")
        print(f"Found {len(result.search_result.papers)} papers")

        if result.search_result.papers:
            print("\nFirst paper:")
            paper = result.search_result.papers[0]
            print(f"Title: {paper.title}")
            print(f"Authors: {[a.name for a in paper.authors]}")
            print(f"Year: {paper.year}")
            print(f"Citation count: {paper.citation_count}")
    except Exception as e:
        print(f"Error processing query: {e}")

    print("\nTest completed.")


if __name__ == "__main__":
    main()
