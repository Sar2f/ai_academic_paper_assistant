#!/usr/bin/env python3
"""
Integration test for the AI Academic Paper Assistant.
Tests the basic functionality without requiring API keys.
"""

import os
import sys
import logging

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.models.paper import Paper, Author, SearchResult, format_author_names  # noqa: E402
from src.llm.processor import LLMProcessor  # noqa: E402
from src.api.semantic_scholar import SemanticScholarAPI  # noqa: E402
from src.utils.config import AppConfig  # noqa: E402
from src.utils.validation import clamp_paper_limit, normalize_search_query  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDataModels:
    """Test the data models."""

    def test_author_creation(self):
        author = Author(name="John Doe", author_id="123", url="https://example.com")
        assert author.name == "John Doe"
        assert author.author_id == "123"

    def test_paper_creation(self):
        author = Author(name="John Doe", author_id="123", url="https://example.com")
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
            fields_of_study=["Computer Science", "AI"],
        )

        assert paper.title == "Test Paper Title"
        assert paper.year == 2024
        assert len(paper.authors) == 1
        assert paper.authors[0].name == "John Doe"

    def test_paper_to_dict(self):
        author = Author(name="John Doe", author_id="123", url="https://example.com")
        paper = Paper(
            paper_id="test123",
            title="Test Paper Title",
            abstract="This is a test abstract.",
            authors=[author],
            year=2024,
            citation_count=10,
            reference_count=20,
            url="https://example.com/paper",
        )
        paper_dict = paper.to_dict()
        assert paper_dict["paper_id"] == "test123"
        assert paper_dict["title"] == "Test Paper Title"

    def test_paper_fields_of_study_default(self):
        """Ensure fields_of_study defaults to empty list, not None."""
        paper = Paper(
            paper_id="test",
            title="Test",
            abstract=None,
            authors=[],
            year=2024,
            citation_count=0,
            reference_count=0,
            url=None,
        )
        assert paper.fields_of_study == []
        assert isinstance(paper.fields_of_study, list)

    def test_format_author_names(self):
        authors = [
            Author(name="A"),
            Author(name="B"),
            Author(name="C"),
            Author(name="D"),
        ]
        assert format_author_names(authors[:2], max_shown=3) == "A, B"
        assert "et al." in format_author_names(authors, max_shown=3)

    def test_normalize_search_query(self):
        assert normalize_search_query(None) is None
        assert normalize_search_query("   ") is None
        assert normalize_search_query("  q  ") == "q"

    def test_clamp_paper_limit(self):
        assert clamp_paper_limit(100, 10) == 20
        assert clamp_paper_limit(0, 5) == 1

    def test_search_result_to_dict(self):
        result = SearchResult(query="test", papers=[], total_results=0, search_time=0.1)
        result_dict = result.to_dict()
        assert result_dict["query"] == "test"
        assert result_dict["total_results"] == 0


class TestConfiguration:
    """Test configuration loading."""

    def test_config_from_env(self):
        os.environ["MAX_PAPERS_TO_RETRIEVE"] = "5"
        os.environ["LLM_MODEL"] = "gpt-3.5-turbo"
        os.environ["TEMPERATURE"] = "0.3"

        try:
            config = AppConfig.from_env()
            assert config.max_papers_to_retrieve == 5
            assert config.llm_model == "gpt-3.5-turbo"
            assert config.temperature == 0.3
        finally:
            del os.environ["MAX_PAPERS_TO_RETRIEVE"]
            del os.environ["LLM_MODEL"]
            del os.environ["TEMPERATURE"]

    def test_config_defaults(self):
        config = AppConfig()
        assert config.max_papers_to_retrieve == 10
        assert config.llm_model == "gpt-4o-mini"
        assert config.temperature == 0.1
        assert config.api_base_url is None

    def test_config_validation_ranges(self):
        config = AppConfig(
            openai_api_key="test-key", max_papers_to_retrieve=100
        )  # Out of range
        with pytest.raises(ValueError):
            config.validate()

    def test_available_models(self):
        config = AppConfig(openai_api_key="test")
        models = config.get_available_models()
        assert "gpt-4o-mini" in models
        assert "gpt-4o" in models
        assert "gpt-4-turbo" in models


class TestPaperProcessing:
    """Test paper processing with mock data."""

    @pytest.fixture
    def mock_papers(self):
        """Create mock papers for testing."""
        authors = [Author(name="Alice Researcher"), Author(name="Bob Scientist")]
        return [
            Paper(
                paper_id="1",
                title="Advances in Neural Networks",
                abstract="This paper discusses recent advances in neural network architectures.",
                authors=authors,
                year=2023,
                citation_count=100,
                reference_count=50,
                url="https://example.com/paper1",
            ),
            Paper(
                paper_id="2",
                title="Transformer Models for NLP",
                abstract="A survey of transformer models and their applications in natural language processing.",
                authors=[Author(name="Charlie Academic")],
                year=2024,
                citation_count=75,
                reference_count=30,
                url="https://example.com/paper2",
            ),
        ]

    def test_context_preparation(self, mock_papers):
        """Test that context is properly prepared from papers."""
        original_openai_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-key"

        try:
            processor = LLMProcessor(model="gpt-3.5-turbo")
            context = processor._prepare_context(mock_papers)

            assert "Advances in Neural Networks" in context
            assert "Transformer Models for NLP" in context
            assert "Alice Researcher" in context
            assert "2023" in context
            assert "2024" in context
        finally:
            if original_openai_key:
                os.environ["OPENAI_API_KEY"] = original_openai_key
            else:
                del os.environ["OPENAI_API_KEY"]

    def test_prompt_creation(self, mock_papers):
        """Test that prompt includes query and critical instructions."""
        original_openai_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-key"

        try:
            processor = LLMProcessor(model="gpt-3.5-turbo")
            context = processor._prepare_context(mock_papers)
            prompt = processor._create_prompt("Test query", context, mock_papers)

            assert "Test query" in prompt
            assert "CRITICAL INSTRUCTIONS" in prompt
        finally:
            if original_openai_key:
                os.environ["OPENAI_API_KEY"] = original_openai_key
            else:
                del os.environ["OPENAI_API_KEY"]

    def test_api_key_from_constructor(self):
        """Test that LLMProcessor accepts API keys from constructor."""
        processor = LLMProcessor(
            model="gpt-3.5-turbo", openai_api_key="test-key-from-constructor"
        )
        assert processor.openai_api_key == "test-key-from-constructor"

    def test_parse_response_citations(self):
        """Test citation parsing from LLM response."""
        original_openai_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-key"

        try:
            processor = LLMProcessor(model="gpt-3.5-turbo")
            response_text = "According to [1], neural networks are powerful. This is supported by [2] and [3]."
            answer, citations = processor._parse_response(response_text)

            assert answer == response_text
            assert 0 in citations  # [1] -> index 0
            assert 1 in citations  # [2] -> index 1
            assert 2 in citations  # [3] -> index 2
        finally:
            if original_openai_key:
                os.environ["OPENAI_API_KEY"] = original_openai_key
            else:
                del os.environ["OPENAI_API_KEY"]





def main():
    """Run all integration tests using pytest."""
    sys.exit(pytest.main([__file__, "-v"]))


if __name__ == "__main__":
    main()
