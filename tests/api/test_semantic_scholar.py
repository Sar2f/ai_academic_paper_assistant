#!/usr/bin/env python3
"""
Test script to check Semantic Scholar API connection.
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.api.semantic_scholar import SemanticScholarAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Test Semantic Scholar API connection."""
    logger.info("Testing Semantic Scholar API connection...")

    # Create API client without API key
    api = SemanticScholarAPI()

    # Test connection
    logger.info("Checking connection...")
    connection_status = api.check_connection()
    logger.info(f"Connection status: {connection_status}")

    # Test search
    logger.info("\nTesting search...")
    search_result = api.search_papers("machine learning", limit=3)
    logger.info(f"Search result: {search_result}")
    logger.info(f"Found {len(search_result.papers)} papers")

    if search_result.papers:
        logger.info("\nFirst paper:")
        paper = search_result.papers[0]
        logger.info(f"Title: {paper.title}")
        logger.info(f"Authors: {[a.name for a in paper.authors]}")
        logger.info(f"Year: {paper.year}")
        logger.info(f"Abstract: {paper.abstract[:100]}..." if paper.abstract else "Abstract: None")

    logger.info("\nTest completed.")


if __name__ == "__main__":
    main()
