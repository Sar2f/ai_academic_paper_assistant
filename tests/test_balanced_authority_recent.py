#!/usr/bin/env python3
"""
Test script to test the balanced authority and recent search functionality.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.orchestrator import AcademicPaperOrchestrator
from src.utils.config_manager import ConfigManager


def test_balanced_authority_recent_search():
    """Test the balanced authority and recent search functionality."""
    print("Testing balanced authority and recent search functionality...")

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Create orchestrator
    orchestrator = AcademicPaperOrchestrator(config)

    # Test search with different limits
    test_queries = [
        ("quantum computing", 20),
        ("machine learning", 20),
        ("artificial intelligence", 20)
    ]

    for query, limit in test_queries:
        print(f"\nTesting search for: {query} (limit: {limit})")
        try:
            result = orchestrator.process_query(query, limit=limit)
            print(f"Found {len(result.search_result.papers)} papers")
            if result.search_result.papers:
                print("First 5 papers:")
                for i, paper in enumerate(result.search_result.papers[:5]):
                    print(f"{i+1}. {paper.title} ({paper.venue}, {paper.year})")
            if result.llm_response.error:
                print(f"LLM Error: {result.llm_response.error}")
            else:
                print("LLM response generated successfully")
                print(f"Answer preview: {result.llm_response.answer[:100]}...")
        except Exception as e:
            print(f"Error processing query: {e}")

    print("\nTest completed.")


if __name__ == "__main__":
    test_balanced_authority_recent_search()
