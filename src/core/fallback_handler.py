import logging
from typing import Optional, List

from .api_manager import APIManager, _deduplicate_papers
from ..models.paper import Paper, SearchResult

logger = logging.getLogger(__name__)


class FallbackHandler:
    """统一的降级处理器"""

    def __init__(self, api_manager: APIManager):
        self.api_manager = api_manager

    def try_fallback_apis(self, query: str, limit: int, sort_by: str = "relevance") -> Optional[SearchResult]:
        """
        尝试使用降级API获取结果，按优先级尝试不同的API组合。

        Returns:
            搜索结果，如果所有API都失败则返回None
        """
        fallback_strategies = [
            ["arxiv", "pubmed"],
            ["pubmed", "openalex"],
            ["arxiv", "openalex"],
            ["semantic_scholar"],
        ]

        for strategy in fallback_strategies:
            try:
                papers: List[Paper] = []
                for api_name in strategy:
                    api = self.api_manager.get_api(api_name)
                    if api:
                        result = api.search_papers(query=query, limit=limit, sort_by=sort_by)
                        papers.extend(result.papers)

                if papers:
                    unique = _deduplicate_papers(papers, limit)
                    logger.info("Fallback strategy %s successful, found %d papers", strategy, len(unique))
                    return SearchResult(
                        query=query,
                        papers=unique,
                        total_results=len(unique),
                        search_time=0,
                    )
            except Exception as e:
                logger.warning("Fallback strategy %s failed: %s", strategy, e)
                continue

        logger.warning("All fallback strategies failed")
        return None
