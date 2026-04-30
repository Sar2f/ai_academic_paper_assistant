#!/usr/bin/env python3
"""
Test script to test the search functionality with arXiv fallback.
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.orchestrator import AcademicPaperOrchestrator
from src.utils.config import AppConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_search():
    """Test search functionality with arXiv fallback."""
    logger.info("Testing search functionality...")

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
        logger.info(f"\nSearching for: {query}")
        try:
            result = orchestrator.process_query(query)
            logger.info(f"Found {len(result.search_result.papers)} papers")

            if result.search_result.papers:
                logger.info("First paper:")
                paper = result.search_result.papers[0]
                logger.info(f"Title: {paper.title}")
                logger.info(f"Authors: {[a.name for a in paper.authors]}")
                logger.info(f"Year: {paper.year}")

            if result.error:
                logger.info(f"Error: {result.error}")
        except Exception as e:
            logger.info(f"Error processing query: {e}")

    logger.info("\nTest completed.")


if __name__ == "__main__":
    test_search()
