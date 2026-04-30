"""
OpenAlex API client.

Only implements _build_connection_test() and _fetch_raw();
retry logic and normalisation are handled by BaseAPI.
"""

import logging
from typing import List, Optional

from .base_api import BaseAPI
from ..models.paper import Paper, SearchResult, Author

logger = logging.getLogger(__name__)


class OpenAlexAPI(BaseAPI):
    """Client for interacting with the OpenAlex API."""

    BASE_URL = "https://api.openalex.org"
    API_NAME = "OpenAlex"

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 0.5):
        super().__init__(api_key=api_key, rate_limit_delay=rate_limit_delay)

    def _build_connection_test(self) -> tuple:
        params = {"search": "test", "per_page": 1, "filter": "abstract:test"}
        if self.api_key:
            params["api_key"] = self.api_key
        return (f"{self.BASE_URL}/works", params, 5)

    def _fetch_raw(
        self,
        query: str,
        limit: int,
        fields: Optional[List[str]],
        year_range: Optional[tuple],
        min_citation_count: Optional[int],
        sort_by: str,
    ) -> SearchResult:
        """Fetch papers from OpenAlex (no retry — handled by BaseAPI)."""
        sort_map = {
            "relevance": None,
            "citedness": "cited_by_count:desc",
            "recent": "publication_year:desc",
        }
        sort_field = sort_map.get(sort_by, None)

        search_params = {"search": query, "per_page": limit}
        if sort_field:
            search_params["sort"] = sort_field

        filters = []
        if year_range:
            min_year, max_year = year_range
            filters.extend([
                f"publication_year:>={min_year}",
                f"publication_year:<={max_year}",
            ])
        if min_citation_count is not None:
            filters.append(f"cited_by_count:>={min_citation_count}")
        if filters:
            search_params["filter"] = ",".join(filters)

        if self.api_key:
            search_params["api_key"] = self.api_key

        response = self.session.get(
            f"{self.BASE_URL}/works", params=search_params, timeout=10
        )
        response.raise_for_status()
        data = response.json()

        papers = []
        for item in data.get("results", []):
            try:
                title = item.get("title", "")
                abstract = item.get("abstract", None)

                authors = []
                for author in item.get("authorships", []):
                    author_name = author.get("author", {}).get("display_name", "")
                    if author_name:
                        authors.append(Author(name=author_name))

                year = item.get("publication_year", None)
                venue = item.get("host_venue", {}).get("display_name", "OpenAlex")
                url = item.get("id", None)
                paper_id = item.get("id", "").split("/")[-1]
                citation_count = item.get("cited_by_count", None)

                papers.append(Paper(
                    paper_id=paper_id,
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    year=year,
                    citation_count=citation_count,
                    url=url,
                    venue=venue,
                ))
            except Exception as e:
                logger.warning("Failed to parse paper data: %s", e)

        return SearchResult(
            query=query,
            papers=papers,
            total_results=len(papers),
            search_time=0,  # set by BaseAPI.search_papers
        )
