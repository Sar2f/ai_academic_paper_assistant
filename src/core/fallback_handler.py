import logging
from typing import Optional, List

from .api_manager import APIManager
from ..models.paper import SearchResult

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
                papers = []
                for api_name in strategy:
                    api = self.api_manager.get_api(api_name)
                    if api:
                        result = api.search_papers(query=query, limit=limit, sort_by=sort_by)
                        papers.extend(result.papers)
                
                if papers:
                    logger.info(f"Fallback strategy {strategy} successful, found {len(papers)} papers")
                    return SearchResult(
                        query=query,
                        papers=papers[:limit],
                        total_results=len(papers),
                        search_time=0
                    )
            except Exception as e:
                logger.warning(f"Fallback strategy {strategy} failed: {e}")
                continue
        
        logger.warning("All fallback strategies failed")
        return None
