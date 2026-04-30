import time
import logging
import xml.etree.ElementTree as ET
from typing import List, Optional
import requests

from .base_api import BaseAPI
from ..models.paper import Paper, SearchResult, Author
from ..utils.validation import normalize_search_query

logger = logging.getLogger(__name__)


class ArxivAPI(BaseAPI):
    """Client for interacting with the arXiv API."""

    BASE_URL = "http://export.arxiv.org/api"

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 3.0):
        """
        Initialize the arXiv API client.

        Args:
            api_key: Optional API key (not required for arXiv)
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
        test_url = f"{self.BASE_URL}/query"
        test_params = {
            "search_query": f"all:{test_query}",
            "max_results": 1
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
                        f"Connected to arXiv API "
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
        Search for papers using the arXiv API.

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

        # Build search query
        search_query = f"all:{query}"
        if year_range:
            min_year, max_year = year_range
            search_query += f" AND submittedDate:[{min_year}0101 TO {max_year}1231]"

        # Map sort_by to arXiv API sort parameters
        sort_map = {
            "relevance": "relevance",
            "citedness": "relevance",  # arXiv doesn't support citation count sorting
            "recent": "submittedDate"
        }
        sort_field = sort_map.get(sort_by, "relevance")
        params = {
            "search_query": search_query,
            "max_results": limit,
            "sortBy": sort_field,
            "sortOrder": "descending"
        }

        # Try up to 3 times with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(f"{self.BASE_URL}/query", params=params, timeout=10)
                response.raise_for_status()

                root = ET.fromstring(response.content)

                papers = []
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                    try:
                        paper_id = entry.find('{http://www.w3.org/2005/Atom}id').text
                        title = entry.find('{http://www.w3.org/2005/Atom}title').text
                        abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text

                        # Parse authors
                        authors = []
                        for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                            author_name = author.find('{http://www.w3.org/2005/Atom}name').text
                            authors.append(author_name)

                        # Parse published date
                        published = entry.find('{http://www.w3.org/2005/Atom}published').text
                        year = int(published.split('-')[0]) if published else None

                        # Create Paper object
                        paper = Paper(
                            paper_id=paper_id,
                            title=title,
                            abstract=abstract,
                            authors=[Author(name=name) for name in authors],
                            year=year,
                            citation_count=None,  # arXiv API doesn't provide citation count
                            reference_count=None,  # arXiv API doesn't provide reference count
                            url=paper_id,
                            venue="arXiv",
                            fields_of_study=[],  # arXiv API doesn't provide fields of study
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
