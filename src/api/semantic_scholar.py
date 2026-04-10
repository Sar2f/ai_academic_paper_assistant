import time
import logging
from typing import List, Optional
import requests

from ..models.paper import Paper, SearchResult
from ..utils.validation import normalize_search_query

logger = logging.getLogger(__name__)


class SemanticScholarAPI:
    """Client for interacting with the Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None,
                 rate_limit_delay: float = 0.1):
        """
        Initialize the Semantic Scholar API client.

        Args:
            api_key: Optional API key for higher rate limits
            rate_limit_delay: Delay between requests to respect rate limits
        """
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"x-api-key": api_key})

    def check_connection(self) -> dict:
        """
        Check if the API is accessible.

        Returns:
            Dictionary with connection status and details
        """
        test_query = "test"
        test_url = f"{self.BASE_URL}/paper/search"
        test_params = {
            "query": test_query,
            "limit": 1,
            "fields": "paperId,title"
        }

        try:
            start_time = time.time()
            response = self.session.get(test_url, params=test_params, timeout=5)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return {
                    "connected": True,
                    "status": "connected",
                    "message": (
                        f"Connected to Semantic Scholar API "
                        f"(response time: {response_time:.2f}s)"
                    ),
                    "response_time": response_time
                }
            elif response.status_code == 429:
                return {
                    "connected": False,
                    "status": "rate_limited",
                    "message": "Rate limited - API is accessible but rate limit reached"
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
        min_citation_count: Optional[int] = None
    ) -> SearchResult:
        """
        Search for papers using the Semantic Scholar API.

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

        if fields is None:
            fields = [
                "paperId", "title", "abstract", "authors", "year",
                "citationCount", "referenceCount", "url", "venue",
                "fieldsOfStudy", "publicationDate"
            ]

        params = {
            "query": query,
            "limit": limit,
            "fields": ",".join(fields),
            "offset": 0
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

        # Try up to 3 times with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(f"{self.BASE_URL}/paper/search", params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                papers = []
                for paper_data in data.get("data", []):
                    try:
                        paper = Paper.from_semantic_scholar(paper_data)
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
                    total_results=data.get("total", 0),
                    search_time=search_time
                )

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 0

                if status_code == 429:  # Rate limited
                    retry_delay = (2 ** attempt) * 0.5  # Exponential backoff: 0.5s, 1s, 2s
                    logger.warning("Rate limited (429) on attempt %d/%d, retrying in %fs...", attempt + 1, max_retries, retry_delay)
                    time.sleep(retry_delay)
                elif status_code >= 500:  # Server error
                    retry_delay = (2 ** attempt) * 0.3
                    logger.warning("Server error (%d) on attempt %d/%d, retrying in %fs...", status_code, attempt + 1, max_retries, retry_delay)
                    time.sleep(retry_delay)
                else:
                    # Client error, don't retry
                    logger.warning("Client error (%d) for query '%s': %s", status_code, query, e)
                    break

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                retry_delay = (2 ** attempt) * 0.5
                logger.warning("Network error on attempt %d/%d, retrying in %fs...", attempt + 1, max_retries, retry_delay)
                time.sleep(retry_delay)

            except requests.exceptions.RequestException as e:
                logger.warning("Request exception for query '%s': %s", query, e)
                break  # Don't retry other request exceptions

        # If we get here, all retries failed
        logger.warning("All %d attempts failed for query '%s'", max_retries, query)
        search_time = time.time() - start_time

        return SearchResult(
            query=query,
            papers=[],
            total_results=0,
            search_time=search_time
        )

    def get_paper_details(self, paper_id: str) -> Optional[Paper]:
        """
        Get detailed information about a specific paper.

        Args:
            paper_id: Semantic Scholar paper ID

        Returns:
            Paper object if found, None otherwise
        """
        fields = [
            "paperId", "title", "abstract", "authors", "year",
            "citationCount", "referenceCount", "url", "venue",
            "fieldsOfStudy", "publicationDate"
        ]

        try:
            response = self.session.get(
                f"{self.BASE_URL}/paper/{paper_id}",
                params={"fields": ",".join(fields)}
            )
            response.raise_for_status()
            paper_data = response.json()

            paper = Paper.from_semantic_scholar(paper_data)

            # Respect rate limits
            time.sleep(self.rate_limit_delay)

            return paper

        except Exception as e:
            logger.error("Error getting paper details for %s: %s", paper_id, e)
            return None

    def get_related_papers(self, paper_id: str, limit: int = 10) -> List[Paper]:
        """
        Get papers related to a specific paper.

        Args:
            paper_id: Semantic Scholar paper ID
            limit: Maximum number of related papers to return

        Returns:
            List of related Paper objects
        """
        fields = [
            "paperId", "title", "abstract", "authors", "year",
            "citationCount", "referenceCount", "url", "venue",
            "fieldsOfStudy", "publicationDate"
        ]

        try:
            response = self.session.get(
                f"{self.BASE_URL}/paper/{paper_id}/references",
                params={"fields": ",".join(fields), "limit": limit}
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            for ref_data in data.get("data", []):
                if "citedPaper" in ref_data:
                    try:
                        paper = Paper.from_semantic_scholar(ref_data["citedPaper"])
                        papers.append(paper)
                    except Exception as e:
                        logger.warning("Failed to parse related paper data: %s", e)
                        continue

            # Respect rate limits
            time.sleep(self.rate_limit_delay)

            return papers

        except requests.exceptions.RequestException as e:
            logger.error("Error getting related papers for %s: %s", paper_id, e)
            return []
