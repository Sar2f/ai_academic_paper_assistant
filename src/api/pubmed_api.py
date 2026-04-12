import time
import logging
from typing import List, Optional
import requests
import xml.etree.ElementTree as ET

from .base_api import BaseAPI
from ..models.paper import Paper, SearchResult, Author
from ..utils.validation import normalize_search_query

logger = logging.getLogger(__name__)


class PubMedAPI(BaseAPI):
    """Client for interacting with the PubMed API."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 0.5):
        """
        Initialize the PubMed API client.

        Args:
            api_key: Optional API key for higher rate limits
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
        test_url = f"{self.BASE_URL}/esearch.fcgi"
        test_params = {
            "db": "pubmed",
            "term": test_query,
            "retmax": 1,
            "retmode": "json"
        }

        if self.api_key:
            test_params["api_key"] = self.api_key

        try:
            start_time = time.time()
            response = self.session.get(test_url, params=test_params, timeout=5)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return {
                    "connected": True,
                    "status": "connected",
                    "message": (
                        f"Connected to PubMed API "
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
        Search for papers using the PubMed API.

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
        search_query = query
        if year_range:
            min_year, max_year = year_range
            search_query += f" AND {min_year}[Date - Publication] : {max_year}[Date - Publication]"

        # First, search for paper IDs
        search_url = f"{self.BASE_URL}/esearch.fcgi"
        # Map sort_by to PubMed API sort parameters
        sort_map = {
            "relevance": "relevance",
            "citedness": "relevance",  # PubMed doesn't support citation count sorting
            "recent": "pubdate"
        }
        sort_field = sort_map.get(sort_by, "relevance")
        search_params = {
            "db": "pubmed",
            "term": search_query,
            "retmax": limit,
            "retmode": "json",
            "sort": sort_field
        }

        if self.api_key:
            search_params["api_key"] = self.api_key

        try:
            # Search for paper IDs
            search_response = self.session.get(search_url, params=search_params, timeout=10)
            search_response.raise_for_status()
            search_data = search_response.json()

            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                return SearchResult(
                    query=query,
                    papers=[],
                    total_results=0,
                    search_time=time.time() - start_time
                )

            # Fetch paper details
            fetch_url = f"{self.BASE_URL}/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "abstract"
            }

            if self.api_key:
                fetch_params["api_key"] = self.api_key

            fetch_response = self.session.get(fetch_url, params=fetch_params, timeout=10)
            fetch_response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(fetch_response.content)

            papers = []
            for article in root.findall(".//PubmedArticle"):
                try:
                    # Extract title
                    title_elem = article.find(".//ArticleTitle")
                    title = title_elem.text if title_elem is not None else ""

                    # Extract abstract
                    abstract_elem = article.find(".//Abstract/AbstractText")
                    abstract = abstract_elem.text if abstract_elem is not None else None

                    # Extract authors
                    authors = []
                    for author in article.findall(".//Author"):
                        last_name = author.find(".//LastName")
                        fore_name = author.find(".//ForeName")
                        if last_name is not None:
                            author_name = last_name.text
                            if fore_name is not None:
                                author_name = f"{fore_name.text} {author_name}"
                            authors.append(Author(name=author_name))

                    # Extract publication date
                    pub_date = article.find(".//PubDate")
                    year = None
                    if pub_date is not None:
                        year_elem = pub_date.find(".//Year")
                        if year_elem is not None:
                            year = int(year_elem.text) if year_elem.text.isdigit() else None

                    # Extract journal
                    journal = article.find(".//Journal/Title")
                    venue = journal.text if journal is not None else "PubMed"

                    # Extract URL
                    pmid = article.find(".//PMID").text
                    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                    # Create Paper object
                    paper = Paper(
                        paper_id=pmid,
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        year=year,
                        citation_count=None,  # PubMed API doesn't provide citation count
                        reference_count=None,  # PubMed API doesn't provide reference count
                        url=url,
                        venue=venue,
                        fields_of_study=[],  # PubMed API doesn't provide fields of study
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
            logger.warning("Error searching PubMed: %s", e)
            search_time = time.time() - start_time
            return SearchResult(
                query=query,
                papers=[],
                total_results=0,
                search_time=search_time
            )
