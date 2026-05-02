import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from ..api.arxiv_api import ArxivAPI
from ..api.openalex_api import OpenAlexAPI
from ..api.pubmed_api import PubMedAPI
from ..api.semantic_scholar import SemanticScholarAPI
from ..models.paper import Paper
from ..utils.config import AppConfig

logger = logging.getLogger(__name__)


class APIManager:
    """Unified interface for managing all academic API clients."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.apis: Dict[str, object] = {}
        self._initialize_apis()

    def _initialize_apis(self):
        self.apis["semantic_scholar"] = SemanticScholarAPI(
            api_key=self.config.semantic_scholar_api_key,
            rate_limit_delay=self.config.rate_limit_delay,
        )
        self.apis["arxiv"] = ArxivAPI(
            rate_limit_delay=self.config.rate_limit_delay * 2,
        )
        self.apis["pubmed"] = PubMedAPI(
            api_key=self.config.pubmed_api_key,
            rate_limit_delay=self.config.rate_limit_delay * 2,
        )
        self.apis["openalex"] = OpenAlexAPI(
            api_key=self.config.openalex_api_key,
            rate_limit_delay=self.config.rate_limit_delay * 2,
        )

    def check_connection(self) -> dict:
        """Check connection status for all APIs."""
        result = {}
        for name, api in self.apis.items():
            try:
                result[name] = api.check_connection()
            except Exception as e:
                logger.warning("Error checking %s API connection: %s", name, e)
                result[name] = {
                    "connected": False,
                    "status": "error",
                    "message": f"Error checking connection: {str(e)}",
                }
        return result

    def search_all_apis(self, query: str, limit: int, sort_by: str = "relevance") -> List[Paper]:
        """Search across all APIs in parallel with deduplication by title."""
        apis = list(self.apis.items())
        num_apis = len(apis)
        papers_per_api = limit // num_apis
        remaining = limit % num_apis

        def _search_one(index: int, name: str, api: object) -> List[Paper]:
            api_limit = papers_per_api + (1 if index < remaining else 0)
            try:
                result = api.search_papers(query=query, limit=api_limit, sort_by=sort_by)
                if result.papers:
                    logger.info("Found %d papers using %s API", len(result.papers), name)
                    return result.papers
                else:
                    logger.info("%s API returned no results", name)
                    return []
            except Exception as e:
                logger.warning("Error using %s API: %s", name, e)
                return []

        all_papers = []
        with ThreadPoolExecutor(max_workers=num_apis) as executor:
            futures = {
                executor.submit(_search_one, i, name, api): name
                for i, (name, api) in enumerate(apis)
            }
            for future in as_completed(futures):
                all_papers.extend(future.result())

        seen_titles: set = set()
        unique_papers = []
        for paper in all_papers:
            if paper.title not in seen_titles:
                seen_titles.add(paper.title)
                unique_papers.append(paper)

        return unique_papers[:limit]

    def get_api(self, api_name: str) -> Optional[object]:
        return self.apis.get(api_name)
