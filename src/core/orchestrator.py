"""
MVP 核心链路（毕设演示建议优先保证以下四点跑通）：
1. Semantic Scholar 论文检索（或模拟数据降级）
2. 基于检索结果的 LLM 作答并解析引用编号
3. Streamlit 配置加载与结果展示
4. 输入校验与异常路径不崩溃
"""

import logging
import time
from typing import Optional
from dataclasses import dataclass

from ..api.semantic_scholar import SemanticScholarAPI
from ..api.arxiv_api import ArxivAPI
from ..api.pubmed_api import PubMedAPI
from ..api.openalex_api import OpenAlexAPI
from ..llm.processor import LLMProcessor, LLMResponse
from ..models.paper import Paper, SearchResult
from ..utils.config import AppConfig
from ..utils.validation import clamp_paper_limit, normalize_search_query

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a query."""

    query: str
    search_result: SearchResult
    llm_response: LLMResponse
    processing_time: float
    error: Optional[str] = None


class AcademicPaperOrchestrator:
    """Orchestrates the entire pipeline: search → process → generate answer."""

    def __init__(self, config: AppConfig):
        """
        Initialize the orchestrator.

        Args:
            config: Application configuration
        """
        self.config = config

        # Initialize components
        self.semantic_scholar = SemanticScholarAPI(
            api_key=config.semantic_scholar_api_key,
            rate_limit_delay=config.rate_limit_delay,
        )

        self.arxiv_api = ArxivAPI(
            rate_limit_delay=config.rate_limit_delay * 2,  # arXiv API has stricter rate limits
        )

        self.pubmed_api = PubMedAPI(
            api_key=config.pubmed_api_key,
            rate_limit_delay=config.rate_limit_delay * 2,  # PubMed API has stricter rate limits
        )

        self.openalex_api = OpenAlexAPI(
            api_key=config.openalex_api_key,
            rate_limit_delay=config.rate_limit_delay * 2,  # OpenAlex API has stricter rate limits
        )

        self.llm_processor = LLMProcessor(
            model=config.llm_model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            openai_api_key=config.openai_api_key,
            api_base_url=config.api_base_url,
        )

    def check_api_connection(self) -> dict:
        """
        Check connection status of all APIs.

        Returns:
            Dictionary with connection status for each API
        """
        result = {
            "semantic_scholar": self.semantic_scholar.check_connection(),
            "arxiv": self.arxiv_api.check_connection(),
            "pubmed": self.pubmed_api.check_connection(),
            "openalex": self.openalex_api.check_connection(),
        }

        # Check OpenAI API if key is configured
        if self.config.openai_api_key:
            result["openai"] = {"configured": True, "status": "key_configured"}
        else:
            result["openai"] = {"configured": False, "status": "no_key"}

        # Check Anthropic API if key is configured
        if self.config.anthropic_api_key:
            result["anthropic"] = {"configured": True, "status": "key_configured"}
        else:
            result["anthropic"] = {"configured": False, "status": "no_key"}

        return result

    def process_query(
        self, query: str, limit: Optional[int] = None
    ) -> ProcessingResult:
        """
        Process a user query through the entire pipeline.

        Args:
            query: User's search query
            limit: Maximum number of papers to retrieve (overrides config)

        Returns:
            ProcessingResult with all data
        """
        start_time = time.time()

        # Validate input types
        if not isinstance(query, str):
            return ProcessingResult(
                query="",
                search_result=SearchResult(
                    query="", papers=[], total_results=0, search_time=0
                ),
                llm_response=LLMResponse(
                    answer="查询必须是字符串类型。",
                    citations=[],
                    error="Invalid query type",
                ),
                processing_time=0,
                error="Invalid query type",
            )

        normalized_query = normalize_search_query(query)
        if not normalized_query:
            return ProcessingResult(
                query=query or "",
                search_result=SearchResult(
                    query=query or "", papers=[], total_results=0, search_time=0
                ),
                llm_response=LLMResponse(
                    answer="请输入有效的检索内容。",
                    citations=[],
                    error="Empty query",
                ),
                processing_time=0,
                error="Empty query",
            )

        try:
            # Step 0: Translate query to academic language
            # Check if query is in Chinese
            is_chinese = any('\u4e00' <= char <= '\u9fff' for char in normalized_query)

            # Translate to English for most APIs, except for Chinese-specific APIs
            if is_chinese:
                translated_query = self.llm_processor.translate_query(normalized_query, target_language="English")
                # For Chinese-specific APIs, use Chinese translation
                chinese_translated_query = self.llm_processor.translate_query(normalized_query, target_language="Chinese")
            else:
                # If query is already in English, just make it more academic
                translated_query = self.llm_processor.translate_query(normalized_query, target_language="English")
                chinese_translated_query = translated_query

            logger.info(f"Original query: {normalized_query}")
            logger.info(f"Translated query: {translated_query}")
            logger.info(f"Chinese translated query: {chinese_translated_query}")

            # Step 1: Search for papers
            total_limit = clamp_paper_limit(
                limit, self.config.max_papers_to_retrieve
            )

            # Try APIs in order of priority
            apis = [
                ("Semantic Scholar", self.semantic_scholar),
                ("arXiv", self.arxiv_api),
                ("PubMed", self.pubmed_api),
                ("OpenAlex", self.openalex_api)
            ]

            # Calculate papers per API for balanced search
            num_apis = len(apis)
            papers_per_api = total_limit // num_apis
            remaining_papers = total_limit % num_apis

            all_papers = []
            total_search_time = 0

            for i, (api_name, api) in enumerate(apis):
                try:
                    # Calculate limit for this API
                    api_limit = papers_per_api
                    if i < remaining_papers:
                        api_limit += 1

                    # Split limit between authoritative and recent papers
                    # Get 60% authoritative papers (by citation count) and 40% recent papers
                    auth_limit = max(1, int(api_limit * 0.6))
                    recent_limit = max(1, api_limit - auth_limit)

                    # Use appropriate query language for each API
                    if api_name in ["CNKI"]:  # Chinese-specific APIs
                        current_query = chinese_translated_query
                    else:  # Most APIs work better with English
                        current_query = translated_query

                    # Search for authoritative papers (by citation count)
                    logger.info(f"Trying {api_name} API for authoritative papers: {current_query} (limit: {auth_limit})")
                    auth_result = api.search_papers(
                        query=current_query, limit=auth_limit, sort_by="citedness"
                    )

                    # Search for recent papers (by publication date)
                    logger.info(f"Trying {api_name} API for recent papers: {current_query} (limit: {recent_limit})")
                    recent_result = api.search_papers(
                        query=current_query, limit=recent_limit, sort_by="recent"
                    )

                    # Combine results
                    if auth_result.papers:
                        all_papers.extend(auth_result.papers)
                        total_search_time += auth_result.search_time
                        logger.info(f"Found {len(auth_result.papers)} authoritative papers using {api_name} API")
                    if recent_result.papers:
                        all_papers.extend(recent_result.papers)
                        total_search_time += recent_result.search_time
                        logger.info(f"Found {len(recent_result.papers)} recent papers using {api_name} API")

                    if not auth_result.papers and not recent_result.papers:
                        logger.info(f"{api_name} API returned no results")
                except Exception as api_error:
                    logger.warning(f"Error using {api_name} API: {api_error}")
                    continue

            # Deduplicate papers based on title
            seen_titles = set()
            unique_papers = []
            for paper in all_papers:
                if paper.title not in seen_titles:
                    seen_titles.add(paper.title)
                    unique_papers.append(paper)

            # Limit to total_limit papers
            final_papers = unique_papers[:total_limit]

            # If no API returned results
            if not final_papers:
                logger.warning("All APIs returned no results")
                search_result = SearchResult(
                    query=normalized_query, papers=[], total_results=0, search_time=0
                )
            else:
                search_result = SearchResult(
                    query=normalized_query,
                    papers=final_papers,
                    total_results=len(final_papers),
                    search_time=total_search_time
                )

            logger.info(
                "Found %d unique papers for query: %s", len(final_papers), normalized_query
            )

            # Step 2: Generate answer using LLM
            llm_response = self.llm_processor.generate_answer(
                query=normalized_query, papers=final_papers
            )

            processing_time = time.time() - start_time

            return ProcessingResult(
                query=normalized_query,
                search_result=search_result,
                llm_response=llm_response,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error("Error processing query '%s': %s", normalized_query, e)
            processing_time = time.time() - start_time

            # Try all APIs as fallback
            search_result = None
            for api_name, api in [
                ("arXiv", self.arxiv_api),
                ("PubMed", self.pubmed_api),
                ("OpenAlex", self.openalex_api)
            ]:
                try:
                    # Use appropriate query language for each API
                    if api_name in ["CNKI"]:  # Chinese-specific APIs
                        current_query = chinese_translated_query
                    else:  # Most APIs work better with English
                        current_query = translated_query

                    result = api.search_papers(
                        query=current_query, limit=clamp_paper_limit(limit, self.config.max_papers_to_retrieve)
                    )
                    if result.papers:
                        search_result = result
                        logger.info(f"Fallback: Found {len(result.papers)} papers using {api_name} API")
                        break
                except Exception as fallback_error:
                    logger.warning(f"Fallback error with {api_name} API: {fallback_error}")
                    continue

            if search_result:
                llm_response = self.llm_processor.generate_answer(
                    query=normalized_query, papers=search_result.papers
                )
                return ProcessingResult(
                    query=normalized_query,
                    search_result=search_result,
                    llm_response=llm_response,
                    processing_time=processing_time,
                    error=f"Primary API failed, using fallback API: {str(e)}",
                )
            else:
                return ProcessingResult(
                    query=normalized_query,
                    search_result=SearchResult(
                        query=query, papers=[], total_results=0, search_time=0
                    ),
                    llm_response=LLMResponse(
                        answer=f"Error processing query: {str(e)}",
                        citations=[],
                        error=str(e),
                    ),
                    processing_time=processing_time,
                    error=str(e),
                )



    def validate_configuration(self) -> bool:
        """Validate that all required components are properly configured."""
        try:
            self.config.validate()

            # Test all APIs
            apis = [
                ("Semantic Scholar", self.semantic_scholar),
                ("arXiv", self.arxiv_api),
                ("PubMed", self.pubmed_api),
                ("OpenAlex", self.openalex_api)
            ]

            accessible_apis = []
            for api_name, api in apis:
                try:
                    test_result = api.search_papers("test", limit=1)
                    if test_result.total_results is not None:
                        accessible_apis.append(api_name)
                        logger.info(f"{api_name} API is accessible")
                except Exception as e:
                    logger.warning(f"{api_name} API test failed: {e}")

            if accessible_apis:
                logger.info(f"Accessible APIs: {', '.join(accessible_apis)}")
            else:
                logger.warning("No APIs are accessible")

            # Test LLM (if API key is available)
            if self.config.openai_api_key or self.config.anthropic_api_key:
                # Create a simple test
                test_papers = [
                    Paper(
                        paper_id="test",
                        title="Test Paper",
                        abstract="This is a test abstract.",
                        authors=[],
                        year=2024,
                        citation_count=0,
                        reference_count=0,
                        url=None,
                    )
                ]

                test_response = self.llm_processor.generate_answer(
                    query="What is this paper about?", papers=test_papers
                )

                if not test_response.error:
                    logger.info(
                        "LLM API is accessible (model: %s)", self.config.llm_model
                    )
                else:
                    logger.warning("LLM API test failed: %s", test_response.error)

            return True

        except Exception as e:
            logger.error("Configuration validation failed: %s", e)
            return False
