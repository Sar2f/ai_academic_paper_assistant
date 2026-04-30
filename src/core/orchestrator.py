"""
Academic Paper Orchestrator - coordinates search, LLM processing, and fallback.
"""

import logging
import time
from typing import Optional, List
from dataclasses import dataclass

from ..llm.processor import LLMProcessor, LLMResponse
from ..models.paper import Paper, SearchResult, CrossPaperAnalysis
from ..utils.config import AppConfig
from ..utils.validation import clamp_paper_limit

from .api_manager import APIManager
from .query_processor import QueryProcessor
from .fallback_handler import FallbackHandler

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a query."""

    query: str
    search_result: SearchResult
    llm_response: LLMResponse
    cross_paper_analysis: CrossPaperAnalysis
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

        # Initialize LLM processor first
        self.llm_processor = LLMProcessor(
            model=config.llm_model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            openai_api_key=config.openai_api_key,
            api_base_url=config.api_base_url,
        )

        # Initialize new components
        self.api_manager = APIManager(config)
        self.query_processor = QueryProcessor(self.llm_processor)
        self.fallback_handler = FallbackHandler(self.api_manager)

    def check_api_connection(self) -> dict:
        """
        Check connection status of all APIs.

        Returns:
            Dictionary with connection status for each API
        """
        result = self.api_manager.check_connection()

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

        # Validate and normalize query
        is_valid, normalized_query, error = self.query_processor.validate_and_normalize(query)
        if not is_valid:
            return ProcessingResult(
                query=query or "",
                search_result=SearchResult(
                    query=query or "", papers=[], total_results=0, search_time=0
                ),
                llm_response=LLMResponse(
                    answer=error,
                    citations=[],
                    error=error,
                ),
                cross_paper_analysis=CrossPaperAnalysis(
                    research_trends="",
                    methodology_comparison="",
                    research_gaps="",
                    future_directions="",
                ),
                processing_time=0,
                error=error,
            )

        try:
            # Translate query
            translated_queries = self.query_processor.translate_query(normalized_query)
            logger.info(f"Original query: {normalized_query}")
            logger.info(f"Translated query: {translated_queries['english']}")
            logger.info(f"Chinese translated query: {translated_queries['chinese']}")

            # Search for papers
            total_limit = clamp_paper_limit(
                limit, self.config.max_papers_to_retrieve
            )

            # Use API manager to search all APIs
            final_papers = self.api_manager.search_all_apis(
                query=translated_queries["english"],
                limit=total_limit,
                sort_by="relevance"
            )

            # Create search result
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
                    search_time=0  # Time is tracked in API manager
                )

            logger.info(
                "Found %d unique papers for query: %s", len(final_papers), normalized_query
            )

            # Generate answer using LLM
            llm_response = self.llm_processor.generate_answer(
                query=normalized_query, papers=final_papers
            )

            # Cross-paper analysis
            cross_paper_analysis = self.llm_processor.cross_paper_analysis(
                query=normalized_query, papers=final_papers
            )

            processing_time = time.time() - start_time

            return ProcessingResult(
                query=normalized_query,
                search_result=search_result,
                llm_response=llm_response,
                cross_paper_analysis=cross_paper_analysis,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error("Error processing query '%s': %s", normalized_query, e)
            processing_time = time.time() - start_time

            # Use fallback handler
            search_result = self.fallback_handler.try_fallback_apis(
                query=translated_queries["english"],
                limit=clamp_paper_limit(limit, self.config.max_papers_to_retrieve)
            )

            if search_result:
                llm_response = self.llm_processor.generate_answer(
                    query=normalized_query, papers=search_result.papers
                )
                cross_paper_analysis = self.llm_processor.cross_paper_analysis(
                    query=normalized_query, papers=search_result.papers
                )
                return ProcessingResult(
                    query=normalized_query,
                    search_result=search_result,
                    llm_response=llm_response,
                    cross_paper_analysis=cross_paper_analysis,
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
                    cross_paper_analysis=CrossPaperAnalysis(
                        research_trends="",
                        methodology_comparison="",
                        research_gaps="",
                        future_directions="",
                    ),
                    processing_time=processing_time,
                    error=str(e),
                )

    def process_followup(self, followup_query: str, papers: List[Paper],
                          previous_answer: str = "") -> LLMResponse:
        """
        Process a follow-up question based on previous search results.

        Args:
            followup_query: User's follow-up question
            papers: List of papers from original search
            previous_answer: Previous answer for context

        Returns:
            LLMResponse with the answer
        """
        return self.llm_processor.handle_followup(
            followup_query=followup_query,
            papers=papers,
            previous_answer=previous_answer
        )

    def validate_configuration(self) -> bool:
        """Validate that all required components are properly configured."""
        try:
            self.config.validate()

            # Test all APIs through API manager
            api_status = self.api_manager.check_connection()
            accessible_apis = [
                name for name, status in api_status.items()
                if status.get("connected", False)
            ]

            if accessible_apis:
                logger.info("Accessible APIs: %s", ", ".join(accessible_apis))
            else:
                logger.warning("No APIs are accessible")

            # Check LLM availability (key existence, no real API call)
            if self.config.openai_api_key or self.config.anthropic_api_key:
                if self.llm_processor.client:
                    logger.info("LLM API key configured (model: %s)", self.config.llm_model)
                else:
                    logger.warning("LLM API key provided but client init failed")
            else:
                logger.warning("No LLM API key — answers will list papers without summary")

            return True

        except Exception as e:
            logger.error("Configuration validation failed: %s", e)
            return False
