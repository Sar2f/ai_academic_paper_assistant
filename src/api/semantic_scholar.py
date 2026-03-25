import time
import logging
import json
from typing import List, Optional
import requests

from ..models.paper import Paper, SearchResult

logger = logging.getLogger(__name__)


class SemanticScholarAPI:
    """Client for interacting with the Semantic Scholar API."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 0.1, use_mock: bool = False):
        """
        Initialize the Semantic Scholar API client.
        
        Args:
            api_key: Optional API key for higher rate limits
            rate_limit_delay: Delay between requests to respect rate limits
            use_mock: Use mock data instead of real API calls (for testing/demo)
        """
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self.use_mock = use_mock
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"x-api-key": api_key})
    
    def _generate_mock_papers(self, query: str, limit: int) -> List[Paper]:
        """Generate mock papers for demonstration purposes."""
        logger.info(f"Generating mock papers for query: {query}")
        
        mock_papers = []
        topics = query.lower().split()
        
        for i in range(min(limit, 5)):  # Generate up to 5 mock papers
            paper_id = f"mock_{i+1}"
            title = f"Advances in {query}: A Comprehensive Review"
            
            if i == 0:
                title = f"Recent Developments in {query}"
            elif i == 1:
                title = f"{query} Applications in Modern Technology"
            elif i == 2:
                title = f"Theoretical Foundations of {query}"
            elif i == 3:
                title = f"Practical Implementations of {query} Algorithms"
            elif i == 4:
                title = f"Future Directions in {query} Research"
            
            abstract = f"This paper provides a comprehensive overview of recent advancements in {query}. "
            abstract += f"The authors discuss key methodologies, applications, and future research directions. "
            abstract += f"Findings suggest significant progress in {query} over the past decade."
            
            authors = [
                {"name": f"Researcher {chr(65+i)}", "authorId": f"author_{i+1}"},
                {"name": f"Professor {chr(66+i)}", "authorId": f"author_{i+2}"}
            ]
            
            year = 2023 - (i % 3)  # Vary years between 2021-2023
            
            paper_data = {
                "paperId": paper_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "year": year,
                "citationCount": 50 + (i * 20),
                "referenceCount": 30 + (i * 10),
                "url": f"https://example.com/paper/{paper_id}",
                "venue": f"Journal of {query} Research",
                "fieldsOfStudy": ["Computer Science", "Artificial Intelligence"],
                "publicationDate": f"{year}-01-01"
            }
            
            try:
                paper = Paper.from_semantic_scholar(paper_data)
                mock_papers.append(paper)
            except Exception as e:
                logger.warning(f"Failed to create mock paper: {e}")
                continue
        
        return mock_papers
    
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
        
        # Use mock data if enabled
        if self.use_mock:
            logger.info(f"Using mock data for query: {query}")
            papers = self._generate_mock_papers(query, limit)
            search_time = time.time() - start_time
            
            return SearchResult(
                query=query,
                papers=papers,
                total_results=len(papers),
                search_time=search_time
            )
        
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
        
        try:
            response = self.session.get(f"{self.BASE_URL}/paper/search", params=params)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for paper_data in data.get("data", []):
                try:
                    paper = Paper.from_semantic_scholar(paper_data)
                    papers.append(paper)
                except Exception as e:
                    logger.warning(f"Failed to parse paper data: {e}")
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
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"API request failed for query '{query}': {e}")
            logger.info(f"Falling back to mock data for query: {query}")
            # Fall back to mock data if API fails
            papers = self._generate_mock_papers(query, limit)
            search_time = time.time() - start_time
            
            return SearchResult(
                query=query,
                papers=papers,
                total_results=len(papers),
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
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting paper details for {paper_id}: {e}")
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
                        logger.warning(f"Failed to parse related paper data: {e}")
                        continue
            
            # Respect rate limits
            time.sleep(self.rate_limit_delay)
            
            return papers
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting related papers for {paper_id}: {e}")
            return []