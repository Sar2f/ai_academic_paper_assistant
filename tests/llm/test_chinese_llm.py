#!/usr/bin/env python3
"""
Test script to test Chinese LLM functionality.
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.llm.processor import LLMProcessor
from src.models.paper import Paper, Author

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_chinese_llm():
    """Test LLM functionality with Chinese queries."""
    logger.info("Testing Chinese LLM functionality...")

    # Create LLM processor with the third-party model service
    llm_processor = LLMProcessor(
        model="DeepSeek-V3.2",
        max_tokens=2000,
        temperature=0.1,
        openai_api_key="sk-3K2lpMnhcUDP7kSNFa74E893Fc2946C39f721cF538A275D5",
        api_base_url="https://api.edgefn.net/v1"
    )

    # Create test papers
    test_papers = [
        Paper(
            paper_id="1",
            title="Advances in Neural Networks",
            abstract="This paper discusses recent advances in neural network architectures and their applications in various domains.",
            authors=[Author(name="John Doe"), Author(name="Jane Smith")],
            year=2023,
            citation_count=100,
            reference_count=50,
            url="https://example.com/paper1",
            venue="Neural Computation",
            fields_of_study=["Computer Science", "AI"],
            publication_date=None
        ),
        Paper(
            paper_id="2",
            title="Transformer Models for NLP",
            abstract="A survey of transformer models and their applications in natural language processing tasks such as translation, summarization, and question answering.",
            authors=[Author(name="Alice Johnson")],
            year=2024,
            citation_count=75,
            reference_count=30,
            url="https://example.com/paper2",
            venue="Journal of NLP Research",
            fields_of_study=["Computer Science", "NLP"],
            publication_date=None
        )
    ]

    # Test generate_answer with Chinese query
    logger.info("Testing generate_answer with Chinese query...")
    try:
        response = llm_processor.generate_answer("神经网络的最新进展是什么？", test_papers)
        logger.info(f"Answer: {response.answer}")
        logger.info(f"Citations: {response.citations}")
        if response.error:
            logger.info(f"Error: {response.error}")
    except Exception as e:
        logger.info(f"Error generating answer: {e}")

    logger.info("\nTest completed.")


if __name__ == "__main__":
    test_chinese_llm()
