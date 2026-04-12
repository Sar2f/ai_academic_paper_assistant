import time
import logging
from typing import List, Optional
import requests

from .base_api import BaseAPI
from ..models.paper import Paper, SearchResult, Author
from ..utils.validation import normalize_search_query

logger = logging.getLogger(__name__)


class OpenAlexAPI(BaseAPI):
    """Client for interacting with the OpenAlex API."""

    BASE_URL = "https://api.openalex.org"

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 0.5):
        """
        Initialize the OpenAlex API client.

        Args:
            api_key: API key for OpenAlex API (optional)
            rate_limit_delay: Delay between requests to respect rate limits
        """
        super().__init__(api_key=api_key, rate_limit_delay=rate_limit_delay)

    def check_connection(self) -> dict:
        """
        Check if the API is accessible.

        Returns:
            Dictionary with connection status and details
        """
        test_query = "test"
        test_url = f"{self.BASE_URL}/works"
        test_params = {
            "search": test_query,
            "per-page": 1,
            "filter": "abstract:test"
        }

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            start_time = time.time()
            response = self.session.get(test_url, params=test_params, headers=headers, timeout=5)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return {
                    "connected": True,
                    "status": "connected",
                    "message": (
                        f"Connected to OpenAlex API "
                        f"(response time: {response_time:.2f}s)"
                    ),
                    "response_time": response_time
                }
            else:
                return {
                    "connected": False,
                    "status": f"error_{response.status_code}",
                    "message": f"API returned status code: {response.status_code}"
                }
        except requests.exceptions.Timeout:
            return {
                "connected": False,
                "status": "timeout",
                "message": "Connection timeout - API not reachable"
            }
        except requests.exceptions.ConnectionError:
            return {
                "connected": False,
                "status": "connection_error",
                "message": "Connection error - network issue or API down"
            }
        except Exception as e:
            return {
                "connected": False,
                "status": "unknown_error",
                "message": f"Unknown error: {str(e)}"
            }

    def search_papers(
        self,
        query: str,
        limit: int = 10,
        fields: Optional[List[str]] = None,
        year_range: Optional[tuple] = None,
        min_citation_count: Optional[int] = None,
        sort_by: str = "relevance"
    ) -> SearchResult:
        """
        Search for papers using the OpenAlex API.

        Args:
            query: Search query string
            limit: Maximum number of papers to return
            fields: List of fields to return (default: basic fields)
            year_range: Tuple of (min_year, max_year) for filtering
            min_citation_count: Minimum citation count for filtering

        Returns:
            SearchResult object containing the papers
        """
        start_time = time.time()

        normalized = normalize_search_query(query)
        if not normalized:
            return SearchResult(
                query=query if isinstance(query, str) else "",
                papers=[],
                total_results=0,
                search_time=time.time() - start_time,
            )

        query = normalized

        # Map sort_by to OpenAlex API sort parameters
        sort_map = {
            "relevance": "relevance",
            "citedness": "cited_by_count:desc",
            "recent": "created:desc"
        }
        sort_field = sort_map.get(sort_by, "relevance")
        # Build search parameters
        search_params = {
            "search": query,
            "per-page": limit,
            "filter": f"abstract:{query}",
            "sort": sort_field
        }

        if year_range:
            min_year, max_year = year_range
            search_params["filter"] += f",publication_year:>={min_year},publication_year:<={max_year}"

        if min_citation_count:
            search_params["filter"] += f",cited_by_count:>={min_citation_count}"

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = self.session.get(f"{self.BASE_URL}/works", params=search_params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            papers = []
            for item in data.get("results", []):
                try:
                    # Extract title
                    title = item.get("title", "")

                    # Extract abstract
                    abstract = item.get("abstract", None)

                    # Extract authors
                    authors = []
                    for author in item.get("authorships", []):
                        author_name = author.get("author", {}).get("display_name", "")
                        if author_name:
                            authors.append(Author(name=author_name))

                    # Extract publication year
                    year = item.get("publication_year", None)

                    # Extract venue
                    venue = item.get("host_venue", {}).get("display_name", "OpenAlex")

                    # Extract URL
                    url = item.get("id", None)

                    # Extract paper ID
                    paper_id = item.get("id", "").split("/")[-1]

                    # Extract citation count
                    citation_count = item.get("cited_by_count", None)

                    # Create Paper object
                    paper = Paper(
                        paper_id=paper_id,
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        year=year,
                        citation_count=citation_count,
                        reference_count=None,  # OpenAlex API doesn't provide reference count
                        url=url,
                        venue=venue,
                        fields_of_study=[],  # OpenAlex API doesn't provide fields of study
                        publication_date=None
                    )
                    papers.append(paper)
                except Exception as e:
                    logger.warning("Failed to parse paper data: %s", e)
                    continue

            # Respect rate limits
            time.sleep(self.rate_limit_delay)

            search_time = time.time() - start_time

            return SearchResult(
                query=query,
                papers=papers,
                total_results=len(papers),
                search_time=search_time
            )

        except Exception as e:
            logger.warning("Error searching OpenAlex: %s", e)
            search_time = time.time() - start_time
            return SearchResult(
                query=query,
                papers=[],
                total_results=0,
                search_time=search_time
            )
