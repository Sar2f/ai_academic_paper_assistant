import time
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

    def _handle_response(self, response):
        """
        Handle API response and raise exceptions for errors.

        Args:
            response: requests.Response object

        Raises:
            requests.exceptions.HTTPError: If the response status code indicates an error
        """
        response.raise_for_status()

    def _retry_with_backoff(self, func, max_retries=3):
        """
        Retry a function with exponential backoff.

        Args:
            func: Function to retry
            max_retries: Maximum number of retries

        Returns:
            Result of the function
        """
        for attempt in range(max_retries):
            try:
                return func()
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
                    raise
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                retry_delay = (2 ** attempt) * 0.5
                logger.warning("Network error on attempt %d/%d, retrying in %fs...", attempt + 1, max_retries, retry_delay)
                time.sleep(retry_delay)
            except requests.exceptions.RequestException as e:
                # Don't retry other request exceptions
                raise

        # If we get here, all retries failed
        raise Exception(f"All {max_retries} attempts failed")
