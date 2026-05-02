import logging
from typing import List, Optional

import requests

from ..models.paper import Paper, SearchResult
from ..utils.validation import normalize_search_query

logger = logging.getLogger(__name__)


class BaseAPI:
    """Base class for academic paper API clients."""

    BASE_URL = ""

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 0.1):
        """
        Initialize the API client.

        Args:
            api_key: Optional API key for higher rate limits
            rate_limit_delay: Delay between requests to respect rate limits
        """
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()

    def check_connection(self) -> dict:
        """
        Check if the API is accessible.

        Returns:
            Dictionary with connection status and details
        """
        raise NotImplementedError("Subclasses must implement check_connection")

    def search_papers(
        self,
        query: str,
        limit: int = 10,
        fields: Optional[List[str]] = None,
        year_range: Optional[tuple] = None,
        min_citation_count: Optional[int] = None
    ) -> SearchResult:
        """
        Search for papers using the API.

        Args:
            query: Search query string
            limit: Maximum number of papers to return
            fields: List of fields to return (default: basic fields)
            year_range: Tuple of (min_year, max_year) for filtering
            min_citation_count: Minimum citation count for filtering

        Returns:
            SearchResult object containing the papers
        """
        raise NotImplementedError("Subclasses must implement search_papers")

