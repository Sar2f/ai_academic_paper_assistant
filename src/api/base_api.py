"""
Base class for academic paper API clients.

Provides common retry logic, connection checking, and rate limiting
so subclasses only need to implement the API-specific parsing.
"""

import re
import time
import logging
from typing import List, Optional

import requests

from ..models.paper import SearchResult
from ..utils.validation import normalize_search_query

logger = logging.getLogger(__name__)


class BaseAPI:
    """Base class for academic paper API clients."""

    BASE_URL = ""
    API_NAME = ""  # Human-readable name used in logs and status dicts

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

    # ------------------------------------------------------------------
    # Connection checking — common implementation
    # ------------------------------------------------------------------

    def check_connection(self) -> dict:
        """
        Check if the API is accessible by sending a lightweight test request.

        Subclasses may override this if they need a completely custom check,
        but the default implementation works for all current APIs.

        Returns:
            Dictionary with connection status and details
        """
        test_url, test_params, test_timeout = self._build_connection_test()

        try:
            start_time = time.time()
            response = self.session.get(
                test_url, params=test_params, timeout=test_timeout
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                return {
                    "connected": True,
                    "status": "connected",
                    "message": (
                        f"Connected to {self.API_NAME} API "
                        f"(response time: {response_time:.2f}s)"
                    ),
                    "response_time": response_time,
                }
            if response.status_code == 429:
                return {
                    "connected": False,
                    "status": "rate_limited",
                    "message": "Rate limited — API is accessible but rate limit reached",
                }
            return {
                "connected": False,
                "status": f"error_{response.status_code}",
                "message": f"API returned status code: {response.status_code}",
            }
        except requests.exceptions.Timeout:
            return {
                "connected": False,
                "status": "timeout",
                "message": "Connection timeout — API not reachable",
            }
        except requests.exceptions.ConnectionError:
            return {
                "connected": False,
                "status": "connection_error",
                "message": "Connection error — network issue or API down",
            }
        except Exception as e:
            return {
                "connected": False,
                "status": "unknown_error",
                "message": f"Unknown error: {e}",
            }

    def _build_connection_test(self) -> tuple:
        """
        Build the URL, params, and timeout for a lightweight connection test.

        Subclasses must override this to provide their test endpoint details.

        Returns:
            (url, params_dict, timeout_seconds)
        """
        raise NotImplementedError("Subclasses must implement _build_connection_test")

    # ------------------------------------------------------------------
    # Search with automatic retry
    # ------------------------------------------------------------------

    def search_papers(
        self,
        query: str,
        limit: int = 10,
        fields: Optional[List[str]] = None,
        year_range: Optional[tuple] = None,
        min_citation_count: Optional[int] = None,
        sort_by: str = "relevance",
    ) -> SearchResult:
        """
        Search for papers using the API.

        Normalises the query, then delegates to the subclass-specific
        _fetch_raw() method with automatic retry/backoff.

        Args:
            query: Search query string
            limit: Maximum number of papers to return
            fields: List of fields to return (default: basic fields)
            year_range: Tuple of (min_year, max_year) for filtering
            min_citation_count: Minimum citation count for filtering
            sort_by: Sort criterion

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

        raw_result = self._search_with_retry(
            normalized, limit, fields, year_range, min_citation_count, sort_by
        )

        # Respect rate limits
        time.sleep(self.rate_limit_delay)

        search_time = time.time() - start_time
        raw_result.query = normalized
        raw_result.search_time = search_time
        return raw_result

    def _search_with_retry(
        self,
        query: str,
        limit: int,
        fields: Optional[List[str]],
        year_range: Optional[tuple],
        min_citation_count: Optional[int],
        sort_by: str,
        max_retries: int = 3,
    ) -> SearchResult:
        """
        Execute _fetch_raw with exponential-backoff retry.

        Retries on 429 (rate-limited), 5xx (server error), Timeout,
        and ConnectionError.  Other HTTP errors and generic
        RequestExceptions are not retried.
        """
        for attempt in range(max_retries):
            try:
                return self._fetch_raw(
                    query, limit, fields, year_range, min_citation_count, sort_by
                )
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 0

                if status_code == 429:
                    delay = (2 ** attempt) * 0.5
                    logger.warning(
                        "Rate limited (429) on attempt %d/%d for %s, retrying in %fs…",
                        attempt + 1, max_retries, self.API_NAME, delay,
                    )
                    time.sleep(delay)
                elif status_code >= 500:
                    delay = (2 ** attempt) * 0.3
                    logger.warning(
                        "Server error (%d) on attempt %d/%d for %s, retrying in %fs…",
                        status_code, attempt + 1, max_retries, self.API_NAME, delay,
                    )
                    time.sleep(delay)
                else:
                    logger.warning(
                        "Client error (%d) for %s query '%s': %s",
                        status_code, self.API_NAME, query, e,
                    )
                    break  # don't retry client errors
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                delay = (2 ** attempt) * 0.5
                logger.warning(
                    "Network error on attempt %d/%d for %s, retrying in %fs…",
                    attempt + 1, max_retries, self.API_NAME, delay,
                )
                time.sleep(delay)
            except requests.exceptions.RequestException as e:
                logger.warning(
                    "Request exception for %s query '%s': %s",
                    self.API_NAME, query, e,
                )
                break

        logger.warning(
            "All %d attempts failed for %s query '%s'",
            max_retries, self.API_NAME, query,
        )
        return SearchResult(query=query, papers=[], total_results=0, search_time=0)

    def _fetch_raw(
        self,
        query: str,
        limit: int,
        fields: Optional[List[str]],
        year_range: Optional[tuple],
        min_citation_count: Optional[int],
        sort_by: str,
    ) -> SearchResult:
        """
        Subclass-specific fetch + parse.

        Must raise requests.exceptions.HTTPError / Timeout / ConnectionError
        so that _search_with_retry can handle retries.

        Returns:
            SearchResult (search_time will be overwritten by search_papers)
        """
        raise NotImplementedError("Subclasses must implement _fetch_raw")
