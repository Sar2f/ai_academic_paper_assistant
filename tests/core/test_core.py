"""Tests for core modules: QueryProcessor, FallbackHandler, Orchestrator."""

import pytest
from unittest.mock import MagicMock

from src.core.query_processor import QueryProcessor
from src.core.fallback_handler import FallbackHandler
from src.core.api_manager import _deduplicate_papers, _normalise_title
from src.models.paper import Paper, Author, SearchResult


class TestQueryProcessor:
    """Tests for QueryProcessor."""

    @pytest.fixture
    def mock_llm(self):
        processor = MagicMock()
        processor.client = None  # No API key
        return processor

    def test_validate_and_normalize_valid(self, mock_llm):
        qp = QueryProcessor(mock_llm)
        ok, norm, err = qp.validate_and_normalize("quantum computing")
        assert ok is True
        assert norm == "quantum computing"
        assert err is None

    def test_validate_and_normalize_empty(self, mock_llm):
        qp = QueryProcessor(mock_llm)
        ok, norm, err = qp.validate_and_normalize("   ")
        assert ok is False
        assert err is not None

    def test_validate_and_normalize_none(self, mock_llm):
        qp = QueryProcessor(mock_llm)
        ok, norm, err = qp.validate_and_normalize(None)
        assert ok is False

    def test_validate_and_normalize_non_string(self, mock_llm):
        qp = QueryProcessor(mock_llm)
        ok, norm, err = qp.validate_and_normalize(123)
        assert ok is False

    def test_translate_query_no_client(self, mock_llm):
        qp = QueryProcessor(mock_llm)
        assert qp.translate_query("test query") == "test query"


class TestFallbackHandler:
    """Tests for FallbackHandler."""

    @pytest.fixture
    def mock_api_manager(self):
        manager = MagicMock()

        # Create mock papers
        paper1 = Paper(
            paper_id="1", title="Paper One", abstract="Abstract 1",
            authors=[Author(name="A")], year=2024, citation_count=10,
        )
        paper2 = Paper(
            paper_id="2", title="Paper Two", abstract="Abstract 2",
            authors=[Author(name="B")], year=2023, citation_count=5,
        )

        result = SearchResult(query="test", papers=[paper1, paper2],
                              total_results=2, search_time=0.1)

        def mock_search(query, limit, sort_by):
            return result

        arxiv_api = MagicMock()
        arxiv_api.search_papers = mock_search
        pubmed_api = MagicMock()
        pubmed_api.search_papers = mock_search
        openalex_api = MagicMock()
        openalex_api.search_papers = mock_search

        manager.get_api = lambda name: {
            "arxiv": arxiv_api,
            "pubmed": pubmed_api,
            "openalex": openalex_api,
        }.get(name)

        return manager

    def test_try_fallback_apis_success(self, mock_api_manager):
        handler = FallbackHandler(mock_api_manager)
        result = handler.try_fallback_apis("test", 10)
        assert result is not None
        assert len(result.papers) > 0

    def test_try_fallback_apis_all_fail(self):
        manager = MagicMock()
        api_mock = MagicMock()
        api_mock.search_papers = MagicMock(side_effect=Exception("API error"))
        manager.get_api = lambda name: api_mock
        handler = FallbackHandler(manager)
        result = handler.try_fallback_apis("test", 10)
        assert result is None


class TestDeduplicatePapers:
    """Tests for _deduplicate_papers."""

    def test_dedup_removes_duplicates(self):
        papers = [
            Paper(paper_id="1", title="Neural Networks", abstract="A",
                  authors=[], year=2024, citation_count=10),
            Paper(paper_id="2", title="neural networks", abstract="B",
                  authors=[], year=2024, citation_count=20),
        ]
        result = _deduplicate_papers(papers, 10)
        assert len(result) == 1

    def test_dedup_keeps_richer_metadata(self):
        papers = [
            Paper(paper_id="1", title="Deep Learning", abstract=None,
                  authors=[], year=2024, citation_count=None),
            Paper(paper_id="2", title="Deep Learning", abstract="Abstract",
                  authors=[], year=2024, citation_count=100),
        ]
        result = _deduplicate_papers(papers, 10)
        assert len(result) == 1
        assert result[0].abstract == "Abstract"

    def test_dedup_respects_limit(self):
        papers = [
            Paper(paper_id=str(i), title=f"Paper {i}", abstract="A",
                  authors=[], year=2024, citation_count=i)
            for i in range(10)
        ]
        result = _deduplicate_papers(papers, 5)
        assert len(result) == 5

    def test_normalise_title_punctuation(self):
        assert _normalise_title("Hello, World!") == _normalise_title("hello world")

    def test_normalise_title_whitespace(self):
        assert _normalise_title("Hello   World") == _normalise_title("hello world")