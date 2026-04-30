#!/usr/bin/env python3
"""
Test script to check Semantic Scholar API status with detailed error information.
"""

import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_semantic_scholar_api():
    """Test Semantic Scholar API with detailed error information."""
    logger.info("Testing Semantic Scholar API...")

    # Test URL
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": "quantum computing",
        "limit": 3,
        "fields": "paperId,title,authors,year"
    }

    try:
        logger.info(f"Request URL: {url}")
        logger.info(f"Params: {params}")

        response = requests.get(url, params=params, timeout=10)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")

        if response.status_code != 200:
            logger.info(f"Error response: {response.text}")
        else:
            data = response.json()
            logger.info(f"Success! Found {data.get('total', 0)} papers")
            if 'data' in data:
                for i, paper in enumerate(data['data'][:3]):
                    logger.info(f"Paper {i+1}: {paper.get('title')}")

    except Exception as e:
        logger.info(f"Exception: {e}")


if __name__ == "__main__":
    test_semantic_scholar_api()
