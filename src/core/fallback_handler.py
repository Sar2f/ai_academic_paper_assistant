import logging
from typing import Optional

from .api_manager import APIManager
from ..models.paper import SearchResult

logger = logging.getLogger(__name__)


class FallbackHandler:
    """Graceful degradation when primary APIs fail."""

    def __init__(self, api_manager: APIManager):
        self.api_manager = api_manager

    def try_fallback_apis(self, query: str, limit: int, sort_by: str = "relevance") -> Optional[SearchResult]:
        """Try fallback API combinations in priority order.

        Returns:
            SearchResult if any strategy succeeds, None if all fail.
        """
        fallback_strategies = [
            ["arxiv", "pubmed"],
            ["pubmed", "openalex"],
            ["arxiv", "openalex"],
            ["semantic_scholar"],
        ]

        for strategy in fallback_strategies:
            try:
                papers = []
                for api_name in strategy:
                    api = self.api_manager.get_api(api_name)
                    if api:
                        result = api.search_papers(query=query, limit=limit, sort_by=sort_by)
                        papers.extend(result.papers)

                if papers:
                    logger.info("Fallback strategy %s successful, found %d papers", strategy, len(papers))
                    return SearchResult(
                        query=query,
                        papers=papers[:limit],
                        total_results=len(papers),
                        search_time=0,
                    )
            except Exception as e:
                logger.warning("Fallback strategy %s failed: %s", strategy, e)

        logger.warning("All fallback strategies failed")
        return None
