import logging
from typing import Optional, List

from .api_manager import APIManager, _normalise_title
from ..models.paper import Paper, SearchResult

logger = logging.getLogger(__name__)


class FallbackHandler:
    """统一的降级处理器"""
    
    def __init__(self, api_manager: APIManager):
        """
        初始化降级处理器
        
        Args:
            api_manager: API管理器实例
        """
        self.api_manager = api_manager
    
    def try_fallback_apis(self, query: str, limit: int, sort_by: str = "relevance") -> Optional[SearchResult]:
        """
        尝试使用降级API获取结果
        
        按优先级尝试不同的API组合，直到成功或全部失败
        
        Args:
            query: 搜索查询
            limit: 最大返回论文数量
            sort_by: 排序方式
            
        Returns:
            搜索结果，如果所有API都失败则返回None
        """
        # 定义降级策略：API优先级列表
        fallback_strategies = [
            ["arxiv", "pubmed"],           # 首选组合
            ["pubmed", "openalex"],        # 备选组合1
            ["arxiv", "openalex"],         # 备选组合2
            ["semantic_scholar"],          # 单一API降级
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
                    # Deduplicate by normalised title (same logic as APIManager)
                    seen: dict = {}
                    for paper in papers:
                        key = _normalise_title(paper.title)
                        if key not in seen:
                            seen[key] = paper
                        else:
                            existing = seen[key]
                            if (paper.abstract and not existing.abstract) or \
                               (paper.citation_count is not None and existing.citation_count is None):
                                seen[key] = paper
                    unique = list(seen.values())[:limit]

                    logger.info("Fallback strategy %s successful, found %d papers", strategy, len(unique))
                    return SearchResult(
                        query=query,
                        papers=unique,
                        total_results=len(unique),
                        search_time=0
                    )
            except Exception as e:
                logger.warning("Fallback strategy %s failed: %s", strategy, e)
                continue
        
        logger.warning("All fallback strategies failed")
        return None
