#!/usr/bin/env python3
"""
Test script to test multiple paper APIs integration.
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.orchestrator import AcademicPaperOrchestrator
from src.utils.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_multiple_apis():
    """Test multiple paper APIs integration."""
    logger.info("Testing multiple paper APIs integration...")

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # Create orchestrator
    orchestrator = AcademicPaperOrchestrator(config)

    # Test API connection
    logger.info("\nTesting API connections...")
    connection_status = orchestrator.check_api_connection()
    for api_name, status in connection_status.items():
        if api_name in ["semantic_scholar", "arxiv", "pubmed", "ieee", "scopus"]:
            if status.get("connected"):
                logger.info(f"{api_name}: Connected ({status.get('response_time', 0):.2f}s)")
            else:
                logger.info(f"{api_name}: Disconnected - {status.get('message', 'Unknown error')}")

    # Test search functionality
    test_queries = ["quantum computing", "machine learning", "artificial intelligence"]

    for query in test_queries:
        logger.info(f"\nTesting search for: {query}")
        try:
            result = orchestrator.process_query(query, limit=5)
            logger.info(f"Found {len(result.search_result.papers)} papers")
            if result.search_result.papers:
                logger.info("First paper:")
                paper = result.search_result.papers[0]
                logger.info(f"Title: {paper.title}")
                logger.info(f"Authors: {[a.name for a in paper.authors]}")
                logger.info(f"Year: {paper.year}")
                logger.info(f"Venue: {paper.venue}")
            if result.llm_response.error:
                logger.info(f"LLM Error: {result.llm_response.error}")
            else:
                logger.info("LLM response generated successfully")
        except Exception as e:
            logger.info(f"Error processing query: {e}")

    logger.info("\nTest completed.")


if __name__ == "__main__":
    test_multiple_apis()
