import logging
from typing import List, Dict, Optional

from ..api.semantic_scholar import SemanticScholarAPI
from ..api.arxiv_api import ArxivAPI
from ..api.pubmed_api import PubMedAPI
from ..api.openalex_api import OpenAlexAPI
from ..models.paper import Paper, SearchResult
from ..utils.config import AppConfig

logger = logging.getLogger(__name__)


class APIManager:
    """管理所有学术API客户端的统一接口"""
    
    def __init__(self, config: AppConfig):
        """
        初始化API管理器
        
        Args:
            config: 应用配置
        """
        self.config = config
        self.apis: Dict[str, object] = {}
        self._initialize_apis()
    
    def _initialize_apis(self):
        """初始化所有API客户端"""
        self.apis["semantic_scholar"] = SemanticScholarAPI(
            api_key=self.config.semantic_scholar_api_key,
            rate_limit_delay=self.config.rate_limit_delay,
        )
        
        self.apis["arxiv"] = ArxivAPI(
            rate_limit_delay=self.config.rate_limit_delay * 2,  # arXiv API has stricter rate limits
        )
        
        self.apis["pubmed"] = PubMedAPI(
            api_key=self.config.pubmed_api_key,
            rate_limit_delay=self.config.rate_limit_delay * 2,  # PubMed API has stricter rate limits
        )
        
        self.apis["openalex"] = OpenAlexAPI(
            api_key=self.config.openalex_api_key,
            rate_limit_delay=self.config.rate_limit_delay * 2,  # OpenAlex API has stricter rate limits
        )
    
    def check_connection(self) -> dict:
        """
        检查所有API的连接状态
        
        Returns:
            包含每个API连接状态的字典
        """
        result = {}
        for name, api in self.apis.items():
            try:
                result[name] = api.check_connection()
            except Exception as e:
                logger.warning(f"Error checking {name} API connection: {e}")
                result[name] = {
                    "connected": False,
                    "status": "error",
                    "message": f"Error checking connection: {str(e)}"
                }
        return result
    
    def search_all_apis(self, query: str, limit: int, sort_by: str = "relevance") -> List[Paper]:
        """
        在所有API中搜索论文并返回合并结果
        
        Args:
            query: 搜索查询
            limit: 最大返回论文数量
            sort_by: 排序方式
            
        Returns:
            合并后的论文列表
        """
        all_papers = []
        num_apis = len(self.apis)
        papers_per_api = limit // num_apis
        remaining_papers = limit % num_apis
        
        for i, (name, api) in enumerate(self.apis.items()):
            api_limit = papers_per_api + (1 if i < remaining_papers else 0)
            try:
                result = api.search_papers(query=query, limit=api_limit, sort_by=sort_by)
                if result.papers:
                    all_papers.extend(result.papers)
                    logger.info(f"Found {len(result.papers)} papers using {name} API")
                else:
                    logger.info(f"{name} API returned no results")
            except Exception as e:
                logger.warning(f"Error using {name} API: {e}")
                continue
        
        # 去重
        seen_titles = set()
        unique_papers = []
        for paper in all_papers:
            if paper.title not in seen_titles:
                seen_titles.add(paper.title)
                unique_papers.append(paper)
        
        return unique_papers[:limit]
    
    def get_api(self, api_name: str) -> Optional[object]:
        """
        获取指定的API客户端
        
        Args:
            api_name: API名称
            
        Returns:
            API客户端实例，如果不存在则返回None
        """
        return self.apis.get(api_name)
