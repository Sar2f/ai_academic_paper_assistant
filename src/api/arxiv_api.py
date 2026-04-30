"""
arXiv API client.

Only implements _build_connection_test() and _fetch_raw();
retry logic and normalisation are handled by BaseAPI.
"""

import logging
import xml.etree.ElementTree as ET
from typing import List, Optional

import requests

from .base_api import BaseAPI
from ..models.paper import Paper, SearchResult, Author

logger = logging.getLogger(__name__)


class ArxivAPI(BaseAPI):
    """Client for interacting with the arXiv API."""

    BASE_URL = "http://export.arxiv.org/api"
    API_NAME = "arXiv"

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 3.0):
        super().__init__(api_key=api_key, rate_limit_delay=rate_limit_delay)

    def _build_connection_test(self) -> tuple:
        return (
            f"{self.BASE_URL}/query",
            {"search_query": "all:test", "max_results": 1},
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
        """Fetch papers from arXiv (no retry — handled by BaseAPI)."""
        # Build search query
        search_query = f"all:{query}"
        if year_range:
            min_year, max_year = year_range
            search_query += f" AND submittedDate:[{min_year}0101 TO {max_year}1231]"

        sort_map = {
            "relevance": "relevance",
            "citedness": "relevance",  # arXiv doesn't support citation sorting
            "recent": "submittedDate",
        }
        sort_field = sort_map.get(sort_by, "relevance")
        params = {
            "search_query": search_query,
            "max_results": limit,
            "sortBy": sort_field,
            "sortOrder": "descending",
        }

        response = self.session.get(f"{self.BASE_URL}/query", params=params, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        papers = []
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            try:
                paper_id = entry.find("{http://www.w3.org/2005/Atom}id").text
                title = entry.find("{http://www.w3.org/2005/Atom}title").text
                abstract = entry.find("{http://www.w3.org/2005/Atom}summary").text

                authors = [
                    author.find("{http://www.w3.org/2005/Atom}name").text
                    for author in entry.findall("{http://www.w3.org/2005/Atom}author")
                ]

                published = entry.find("{http://www.w3.org/2005/Atom}published").text
                year = int(published.split("-")[0]) if published else None

                papers.append(Paper(
                    paper_id=paper_id,
                    title=title,
                    abstract=abstract,
                    authors=[Author(name=name) for name in authors],
                    year=year,
                    citation_count=None,
                    reference_count=None,
                    url=paper_id,
                    venue="arXiv",
                    fields_of_study=[],
                    publication_date=None,
                ))
            except Exception as e:
                logger.warning("Failed to parse paper data: %s", e)

        return SearchResult(
            query=query,
            papers=papers,
            total_results=len(papers),
            search_time=0,  # set by BaseAPI.search_papers
        )
