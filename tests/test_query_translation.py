#!/usr/bin/env python3
"""
Test script to test query translation functionality.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.llm.processor import LLMProcessor


def test_query_translation():
    """Test query translation functionality."""
    print("Testing query translation functionality...")

    # Create LLM processor
    llm_processor = LLMProcessor(
        model="DeepSeek-V3.2",
        max_tokens=2000,
        temperature=0.1,
        openai_api_key="sk-3K2lpMnhcUDP7kSNFa74E893Fc2946C39f721cF538A275D5",
        api_base_url="https://api.edgefn.net/v1"
    )

    # Test Chinese queries
    test_queries = [
        "神经网络是怎么工作的",
        "机器学习有哪些应用",
        "人工智能未来发展趋势"
    ]

    for query in test_queries:
        print(f"\nOriginal query: {query}")

        # Translate to English
        english_translation = llm_processor.translate_query(query, target_language="English")
        print(f"English translation: {english_translation}")

        # Translate to Chinese academic language
        chinese_translation = llm_processor.translate_query(query, target_language="Chinese")
        print(f"Chinese academic translation: {chinese_translation}")

    # Test English queries
    print("\n\nTesting English queries...")
    english_queries = [
        "how do neural networks work",
        "what are the applications of machine learning",
        "future trends in artificial intelligence"
    ]

    for query in english_queries:
        print(f"\nOriginal query: {query}")

        # Make it more academic
        academic_translation = llm_processor.translate_query(query, target_language="English")
        print(f"Academic translation: {academic_translation}")

    print("\nTest completed.")


if __name__ == "__main__":
    test_query_translation()
