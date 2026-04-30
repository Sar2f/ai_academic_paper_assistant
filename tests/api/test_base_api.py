"""Unit tests for BaseAPI refactoring and API Manager deduplication."""

from unittest.mock import patch, MagicMock

from src.api.base_api import BaseAPI
from src.core.api_manager import _normalise_title
from src.models.paper import Paper, SearchResult


# ---------------------------------------------------------------------------
# BaseAPI abstract contract
# ---------------------------------------------------------------------------

class ConcreteAPI(BaseAPI):
    """Concrete subclass for testing BaseAPI behaviour."""

    BASE_URL = "https://example.com"
    API_NAME = "TestAPI"

    def _build_connection_test(self):
        return (self.BASE_URL + "/test", {"q": "test"}, 5)

    def _fetch_raw(self, query, limit, fields, year_range, min_citation_count, sort_by):
        # Simulate a successful response
        return SearchResult(
            query=query,
            papers=[Paper(
                paper_id="1", title="Test Paper", abstract="Abstract",
                authors=[], year=2024, citation_count=0, reference_count=0,
            )],
            total_results=1,
            search_time=0,
        )


class TestBaseAPI:
    """Test BaseAPI common functionality."""

    def test_api_name_attribute(self):
        api = ConcreteAPI()
        assert api.API_NAME == "TestAPI"

    def test_search_papers_normalises_query(self):
        api = ConcreteAPI(rate_limit_delay=0)
        result = api.search_papers("  hello world  ")
        assert result.query == "hello world"

    def test_search_papers_rejects_empty_query(self):
        api = ConcreteAPI(rate_limit_delay=0)
        result = api.search_papers("   ")
        assert result.papers == []
        assert result.total_results == 0

    def test_search_papers_rejects_none_query(self):
        api = ConcreteAPI(rate_limit_delay=0)
        result = api.search_papers(None)
        assert result.papers == []

    def test_search_papers_returns_result(self):
        api = ConcreteAPI(rate_limit_delay=0)
        result = api.search_papers("quantum")
        assert len(result.papers) == 1
        assert result.papers[0].title == "Test Paper"

    def test_search_with_retry_on_server_error(self):
        """Test that _search_with_retry retries on server errors."""
        api = ConcreteAPI(rate_limit_delay=0)
        call_count = 0

        def failing_fetch_raw(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                import requests as req
                resp = MagicMock()
                resp.status_code = 500
                resp.raise_for_status.side_effect = req.exceptions.HTTPError(response=resp)
                raise resp.raise_for_status()
            return SearchResult(
                query="test", papers=[], total_results=0, search_time=0
            )

        api._fetch_raw = failing_fetch_raw
        with patch("src.api.base_api.time.sleep"):
            api._search_with_retry("test", 10, None, None, None, "relevance")
        assert call_count == 2  # 1 fail + 1 success


# ---------------------------------------------------------------------------
# Title normalisation for dedup
# ---------------------------------------------------------------------------

class TestTitleNormalisation:
    """Test title normalisation for fuzzy deduplication."""

    def test_case_insensitive(self):
        assert _normalise_title("Hello World") == _normalise_title("hello world")

    def test_whitespace_normalised(self):
        assert _normalise_title("Hello   World") == _normalise_title("Hello World")

    def test_punctuation_stripped(self):
        assert _normalise_title("Hello, World!") == _normalise_title("hello world")

    def test_identical_after_normalise(self):
        assert _normalise_title("A Survey of Neural Networks") == \
               _normalise_title("a survey of neural networks")

    def test_different_titles_differ(self):
        assert _normalise_title("Neural Networks") != _normalise_title("Deep Learning")