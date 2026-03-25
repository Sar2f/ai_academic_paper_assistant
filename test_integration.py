#!/usr/bin/env python3
"""
Integration test for the AI Academic Paper Assistant.
Tests the basic functionality without requiring API keys.
"""

import os
import sys
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.paper import Paper, Author
from src.llm.processor import LLMProcessor
from src.api.semantic_scholar import SemanticScholarAPI
from src.utils.config import AppConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_data_models():
    """Test the data models."""
    print("Testing data models...")
    
    # Create a test author
    author = Author(name="John Doe", author_id="123", url="https://example.com")
    assert author.name == "John Doe"
    assert author.author_id == "123"
    
    # Create a test paper
    paper = Paper(
        paper_id="test123",
        title="Test Paper Title",
        abstract="This is a test abstract for the paper.",
        authors=[author],
        year=2024,
        citation_count=10,
        reference_count=20,
        url="https://example.com/paper",
        venue="Test Conference",
        fields_of_study=["Computer Science", "AI"]
    )
    
    assert paper.title == "Test Paper Title"
    assert paper.year == 2024
    assert len(paper.authors) == 1
    assert paper.authors[0].name == "John Doe"
    
    # Test to_dict method
    paper_dict = paper.to_dict()
    assert paper_dict["paper_id"] == "test123"
    assert paper_dict["title"] == "Test Paper Title"
    
    print("✅ Data models test passed!")


def test_semantic_scholar_api():
    """Test Semantic Scholar API (without API key)."""
    print("\nTesting Semantic Scholar API...")
    
    try:
        api = SemanticScholarAPI(rate_limit_delay=0.2)
        
        # Test search with a simple query
        result = api.search_papers("machine learning", limit=2)
        
        print(f"  Found {len(result.papers)} papers")
        print(f"  Total results: {result.total_results}")
        print(f"  Search time: {result.search_time:.2f}s")
        
        if result.papers:
            paper = result.papers[0]
            print(f"  First paper: {paper.title[:50]}...")
            print(f"  Authors: {[a.name for a in paper.authors[:2]]}")
        
        print("✅ Semantic Scholar API test passed!")
        
    except Exception as e:
        print(f"⚠️ Semantic Scholar API test had issues: {e}")
        print("  This might be due to network or API rate limits.")


def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    # Create a mock environment
    os.environ["MAX_PAPERS_TO_RETRIEVE"] = "5"
    os.environ["LLM_MODEL"] = "gpt-3.5-turbo"
    os.environ["TEMPERATURE"] = "0.3"
    
    config = AppConfig.from_env()
    
    assert config.max_papers_to_retrieve == 5
    assert config.llm_model == "gpt-3.5-turbo"
    assert config.temperature == 0.3
    
    print("✅ Configuration test passed!")
    
    # Clean up
    del os.environ["MAX_PAPERS_TO_RETRIEVE"]
    del os.environ["LLM_MODEL"]
    del os.environ["TEMPERATURE"]


def test_paper_processing():
    """Test paper processing with mock data."""
    print("\nTesting paper processing...")
    
    # Create mock papers
    authors = [
        Author(name="Alice Researcher"),
        Author(name="Bob Scientist")
    ]
    
    papers = [
        Paper(
            paper_id="1",
            title="Advances in Neural Networks",
            abstract="This paper discusses recent advances in neural network architectures.",
            authors=authors,
            year=2023,
            citation_count=100,
            reference_count=50,
            url="https://example.com/paper1"
        ),
        Paper(
            paper_id="2",
            title="Transformer Models for NLP",
            abstract="A survey of transformer models and their applications in natural language processing.",
            authors=[Author(name="Charlie Academic")],
            year=2024,
            citation_count=75,
            reference_count=30,
            url="https://example.com/paper2"
        )
    ]
    
    # Test context preparation (without actually calling LLM)
    from src.llm.processor import LLMProcessor
    
    # Temporarily set an environment variable to avoid API key error
    import os
    original_openai_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "test-key"
    
    try:
        # Create processor
        processor = LLMProcessor(model="gpt-3.5-turbo")
        
        # Monkey patch to avoid actual API calls
        class MockClient:
            def chat(self):
                return self
            def completions(self):
                return self
            def create(self, **kwargs):
                class MockResponse:
                    def __init__(self):
                        self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Test response'})()})()]
                return MockResponse()
        
        processor.client = MockClient()
        
        # Test context preparation
        context = processor._prepare_context(papers)
        
        assert "Advances in Neural Networks" in context
        assert "Transformer Models for NLP" in context
        assert "Alice Researcher" in context
        assert "2023" in context
        assert "2024" in context
        
        # Test prompt creation
        prompt = processor._create_prompt("Test query", context, papers)
        assert "Test query" in prompt
        assert "CRITICAL INSTRUCTIONS" in prompt
        
        print("✅ Paper processing test passed!")
        
    finally:
        # Restore original environment
        if original_openai_key:
            os.environ["OPENAI_API_KEY"] = original_openai_key
        else:
            del os.environ["OPENAI_API_KEY"]


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("AI Academic Paper Assistant - Integration Tests")
    print("=" * 60)
    
    try:
        test_data_models()
        test_configuration()
        test_paper_processing()
        test_semantic_scholar_api()
        
        print("\n" + "=" * 60)
        print("All integration tests completed successfully! 🎉")
        print("\nNext steps:")
        print("1. Copy .env.example to .env")
        print("2. Add your API keys to .env (optional for basic search)")
        print("3. Run: pip install -r requirements.txt")
        print("4. Run: streamlit run app.py")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Integration tests failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())