#!/usr/bin/env python3
"""
Test script to test the balanced authority and recent search functionality.
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.orchestrator import AcademicPaperOrchestrator
from src.utils.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_balanced_authority_recent_search():
    """Test the balanced authority and recent search functionality."""
    logger.info("Testing balanced authority and recent search functionality...")

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
        logger.info(f"\nTesting search for: {query} (limit: {limit})")
        try:
            result = orchestrator.process_query(query, limit=limit)
            logger.info(f"Found {len(result.search_result.papers)} papers")
            if result.search_result.papers:
                logger.info("First 5 papers:")
                for i, paper in enumerate(result.search_result.papers[:5]):
                    logger.info(f"{i+1}. {paper.title} ({paper.venue}, {paper.year})")
            if result.llm_response.error:
                logger.info(f"LLM Error: {result.llm_response.error}")
            else:
                logger.info("LLM response generated successfully")
                logger.info(f"Answer preview: {result.llm_response.answer[:100]}...")
        except Exception as e:
            logger.info(f"Error processing query: {e}")

    logger.info("\nTest completed.")


if __name__ == "__main__":
    test_balanced_authority_recent_search()
