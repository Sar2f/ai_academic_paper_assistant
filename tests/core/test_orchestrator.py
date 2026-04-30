#!/usr/bin/env python3
"""
Test script to check orchestrator functionality without API keys.
"""

import sys
import os
import logging

# Add project root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.core.orchestrator import AcademicPaperOrchestrator
from src.utils.config import AppConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Test orchestrator functionality."""
    logger.info("Testing orchestrator functionality...")

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
    logger.info("Checking API connections...")
    connection_status = orchestrator.check_api_connection()
    logger.info(f"Semantic Scholar status: {connection_status['semantic_scholar']}")

    # Test search
    logger.info("\nTesting search...")
    try:
        result = orchestrator.process_query("machine learning")
        logger.info(f"Processing result: {result}")
        logger.info(f"Found {len(result.search_result.papers)} papers")

        if result.search_result.papers:
            logger.info("\nFirst paper:")
            paper = result.search_result.papers[0]
            logger.info(f"Title: {paper.title}")
            logger.info(f"Authors: {[a.name for a in paper.authors]}")
            logger.info(f"Year: {paper.year}")
            logger.info(f"Citation count: {paper.citation_count}")
    except Exception as e:
        logger.info(f"Error processing query: {e}")

    logger.info("\nTest completed.")


if __name__ == "__main__":
    main()
