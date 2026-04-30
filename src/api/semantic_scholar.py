"""
Semantic Scholar API client.

Only implements _build_connection_test() and _fetch_raw();
retry logic and normalisation are handled by BaseAPI.
"""

import logging
from typing import List, Optional

import requests

from .base_api import BaseAPI
from ..models.paper import Paper, SearchResult

logger = logging.getLogger(__name__)


class SemanticScholarAPI(BaseAPI):
    """Client for interacting with the Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    API_NAME = "Semantic Scholar"

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 0.1):
        super().__init__(api_key=api_key, rate_limit_delay=rate_limit_delay)
        if api_key:
            self.session.headers.update({"x-api-key": api_key})

    def _build_connection_test(self) -> tuple:
        return (
            f"{self.BASE_URL}/paper/search",
            {"query": "test", "limit": 1, "fields": "paperId,title"},
            5,
        )

    def _fetch_raw(
        self,
        query: str,
        limit: int,
        fields: Optional[List[str]],
        year_range: Optional[tuple],
        min_citation_count: Optional[int],
        sort_by: str,
    ) -> SearchResult:
        """Fetch papers from Semantic Scholar (no retry — handled by BaseAPI)."""
        if fields is None:
            fields = [
                "paperId", "title", "abstract", "authors", "year",
                "citationCount", "referenceCount", "url", "venue",
                "fieldsOfStudy", "publicationDate",
            ]

        # Map sort_by to Semantic Scholar API sort parameters
        sort_map = {"relevance": "relevance", "citedness": "citedness", "recent": "recency"}
        sort_field = sort_map.get(sort_by, "relevance")

        params = {
            "query": query,
            "limit": limit,
            "fields": ",".join(fields),
            "offset": 0,
            "sort": sort_field,
        }

        # Add filters if provided
        filters = []
        if year_range:
            min_year, max_year = year_range
            filters.append(f"year:[{min_year} TO {max_year}]")
        if min_citation_count is not None:
            filters.append(f"citationCount:>={min_citation_count}")
        if filters:
            params["filter"] = ",".join(filters)

        response = self.session.get(f"{self.BASE_URL}/paper/search", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        papers = []
        for paper_data in data.get("data", []):
            try:
                papers.append(Paper.from_semantic_scholar(paper_data))
            except Exception as e:
                logger.warning("Failed to parse paper data: %s", e)

        return SearchResult(
            query=query,
            papers=papers,
            total_results=data.get("total", 0),
            search_time=0,  # set by BaseAPI.search_papers
        )


