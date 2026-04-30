"""
Unified manager for all academic API clients.

Features:
  - Title-normalised deduplication (case + whitespace)
  - Concurrent API searching via ThreadPoolExecutor
"""

import re
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..api.semantic_scholar import SemanticScholarAPI
from ..api.arxiv_api import ArxivAPI
from ..api.pubmed_api import PubMedAPI
from ..api.openalex_api import OpenAlexAPI
from ..models.paper import Paper
from ..utils.config import AppConfig

logger = logging.getLogger(__name__)

# Pre-compiled regex for title normalisation
_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")


def _normalise_title(title: str) -> str:
    """Normalise a paper title for fuzzy dedup comparison."""
    t = _PUNCT_RE.sub("", title.lower())
    return _WHITESPACE_RE.sub(" ", t).strip()


def _deduplicate_papers(papers: List[Paper], limit: int) -> List[Paper]:
    """Deduplicate papers by normalised title, keeping richer metadata on collision."""
    seen: Dict[str, Paper] = {}
    for paper in papers:
        key = _normalise_title(paper.title)
        if key not in seen:
            seen[key] = paper
        else:
            existing = seen[key]
            if (paper.abstract and not existing.abstract) or \
               (paper.citation_count is not None and existing.citation_count is None):
                seen[key] = paper
    return list(seen.values())[:limit]


class APIManager:
    """管理所有学术API客户端的统一接口"""

    def __init__(self, config: AppConfig, max_workers: int = 4):
        """
        初始化API管理器

        Args:
            config: 应用配置
            max_workers: 并发搜索线程数
        """
        self.config = config
        self.max_workers = max_workers
        self.apis: Dict[str, object] = {}
        self._initialize_apis()

    def _initialize_apis(self):
        """初始化所有API客户端"""
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
        """检查所有API的连接状态"""
        result = {}
        for name, api in self.apis.items():
            try:
                result[name] = api.check_connection()
            except Exception as e:
                logger.warning("Error checking %s API connection: %s", name, e)
                result[name] = {
                    "connected": False,
                    "status": "error",
                    "message": f"Error checking connection: {e}",
                }
        return result

    def search_all_apis(self, query: str, limit: int, sort_by: str = "relevance") -> List[Paper]:
        """
        在所有API中并发搜索论文并返回去重合并结果

        Args:
            query: 搜索查询
            limit: 最大返回论文数量
            sort_by: 排序方式

        Returns:
            合并去重后的论文列表
        """
        num_apis = len(self.apis)
        papers_per_api = limit // num_apis
        remaining = limit % num_apis

        # Distribute limit evenly across APIs
        api_limits = {}
        for i, name in enumerate(self.apis):
            api_limits[name] = papers_per_api + (1 if i < remaining else 0)

        # Search all APIs concurrently
        all_papers: List[Paper] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    api.search_papers, query=query, limit=api_limits[name], sort_by=sort_by
                ): name
                for name, api in self.apis.items()
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    if result.papers:
                        all_papers.extend(result.papers)
                        logger.info("Found %d papers using %s API", len(result.papers), name)
                    else:
                        logger.info("%s API returned no results", name)
                except Exception as e:
                    logger.warning("Error using %s API: %s", name, e)

        # Deduplicate by normalised title
        return _deduplicate_papers(all_papers, limit)

    def get_api(self, api_name: str) -> Optional[object]:
        """获取指定的API客户端"""
        return self.apis.get(api_name)
