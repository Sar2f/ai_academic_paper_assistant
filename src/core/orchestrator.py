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
            use_mock=config.use_mock_data,
        )

        self.llm_processor = LLMProcessor(
            model=config.llm_model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            openai_api_key=config.openai_api_key,
            anthropic_api_key=config.anthropic_api_key,
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
            "use_mock_data": self.config.use_mock_data,
        }

        # Check LLM APIs if keys are configured
        if self.config.openai_api_key:
            result["openai"] = {"configured": True, "status": "key_configured"}
        else:
            result["openai"] = {"configured": False, "status": "no_key"}

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
            # Step 1: Search for papers
            search_limit = clamp_paper_limit(
                limit, self.config.max_papers_to_retrieve
            )
            search_result = self.semantic_scholar.search_papers(
                query=normalized_query, limit=search_limit
            )

            logger.info(
                f"Found {len(search_result.papers)} papers for query: {normalized_query}"
            )

            # Step 2: Generate answer using LLM
            llm_response = self.llm_processor.generate_answer(
                query=normalized_query, papers=search_result.papers
            )

            processing_time = time.time() - start_time

            return ProcessingResult(
                query=normalized_query,
                search_result=search_result,
                llm_response=llm_response,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Error processing query '{normalized_query}': {e}")
            processing_time = time.time() - start_time

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

    def get_paper_summaries(self, papers: list[Paper]) -> dict[str, str]:
        """
        Generate summaries for multiple papers.

        Args:
            papers: List of papers to summarize

        Returns:
            Dictionary mapping paper IDs to summaries
        """
        summaries = {}

        for paper in papers:
            try:
                summary = self.llm_processor.summarize_paper(paper)
                summaries[paper.paper_id] = summary
            except Exception as e:
                logger.error(f"Error summarizing paper {paper.paper_id}: {e}")
                summaries[paper.paper_id] = f"Summary unavailable: {str(e)}"

        return summaries

    def validate_configuration(self) -> bool:
        """Validate that all required components are properly configured."""
        try:
            self.config.validate()

            # Test Semantic Scholar API
            test_result = self.semantic_scholar.search_papers("test", limit=1)
            if test_result.total_results is not None:
                logger.info("Semantic Scholar API is accessible")

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
                        f"LLM API is accessible (model: {self.config.llm_model})"
                    )
                else:
                    logger.warning(f"LLM API test failed: {test_response.error}")

            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
