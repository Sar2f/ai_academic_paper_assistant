#!/usr/bin/env python3
"""
Test script to check Semantic Scholar API status with detailed error information.
"""

import requests
import json


def test_semantic_scholar_api():
    """Test Semantic Scholar API with detailed error information."""
    print("Testing Semantic Scholar API...")

    # Test URL
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": "quantum computing",
        "limit": 3,
        "fields": "paperId,title,authors,year"
    }

    try:
        print(f"Request URL: {url}")
        print(f"Params: {params}")

        response = requests.get(url, params=params, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
        else:
            data = response.json()
            print(f"Success! Found {data.get('total', 0)} papers")
            if 'data' in data:
                for i, paper in enumerate(data['data'][:3]):
                    print(f"Paper {i+1}: {paper.get('title')}")

    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    test_semantic_scholar_api()
