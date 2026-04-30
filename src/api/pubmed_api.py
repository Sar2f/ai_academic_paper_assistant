"""
PubMed API client.

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


class PubMedAPI(BaseAPI):
    """Client for interacting with the PubMed API."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    API_NAME = "PubMed"

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 0.5):
        super().__init__(api_key=api_key, rate_limit_delay=rate_limit_delay)

    def _build_connection_test(self) -> tuple:
        params = {"db": "pubmed", "term": "test", "retmax": 1, "retmode": "json"}
        if self.api_key:
            params["api_key"] = self.api_key
        return (f"{self.BASE_URL}/esearch.fcgi", params, 5)

    def _fetch_raw(
        self,
        query: str,
        limit: int,
        fields: Optional[List[str]],
        year_range: Optional[tuple],
        min_citation_count: Optional[int],
        sort_by: str,
    ) -> SearchResult:
        """Fetch papers from PubMed (no retry — handled by BaseAPI)."""
        search_query = query
        if year_range:
            min_year, max_year = year_range
            search_query += f" AND ({min_year}:{max_year})[Date - Publication]"

        sort_map = {"relevance": "relevance", "citedness": "relevance", "recent": "pubdate"}
        sort_field = sort_map.get(sort_by, "relevance")

        search_params = {
            "db": "pubmed",
            "term": search_query,
            "retmax": limit,
            "retmode": "json",
            "sort": sort_field,
        }
        if self.api_key:
            search_params["api_key"] = self.api_key

        # Step 1: search for paper IDs
        search_response = self.session.get(
            f"{self.BASE_URL}/esearch.fcgi", params=search_params, timeout=10
        )
        search_response.raise_for_status()
        search_data = search_response.json()

        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return SearchResult(query=query, papers=[], total_results=0, search_time=0)

        # Step 2: fetch paper details
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }
        if self.api_key:
            fetch_params["api_key"] = self.api_key

        fetch_response = self.session.get(
            f"{self.BASE_URL}/efetch.fcgi", params=fetch_params, timeout=10
        )
        fetch_response.raise_for_status()

        root = ET.fromstring(fetch_response.content)
        papers = []
        for article in root.findall(".//PubmedArticle"):
            try:
                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else ""

                abstract_elem = article.find(".//Abstract/AbstractText")
                abstract = abstract_elem.text if abstract_elem is not None else None

                authors = []
                for author in article.findall(".//Author"):
                    last_name = author.find(".//LastName")
                    fore_name = author.find(".//ForeName")
                    if last_name is not None:
                        author_name = last_name.text
                        if fore_name is not None:
                            author_name = f"{fore_name.text} {author_name}"
                        authors.append(Author(name=author_name))

                year = None
                pub_date = article.find(".//PubDate")
                if pub_date is not None:
                    year_elem = pub_date.find(".//Year")
                    if year_elem is not None and year_elem.text.isdigit():
                        year = int(year_elem.text)

                journal = article.find(".//Journal/Title")
                venue = journal.text if journal is not None else "PubMed"

                pmid = article.find(".//PMID").text
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                papers.append(Paper(
                    paper_id=pmid,
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    year=year,
                    citation_count=None,
                    reference_count=None,
                    url=url,
                    venue=venue,
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
