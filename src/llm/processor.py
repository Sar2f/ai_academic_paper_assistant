import json
import os
import re
import logging
from typing import List, Optional
from dataclasses import dataclass

from ..models.paper import Paper, format_author_names, PaperAnalysis, CrossPaperAnalysis
from .prompts import ANSWER_PROMPT, ANALYSIS_PROMPT, CROSS_PAPER_PROMPT, FOLLOWUP_PROMPT, TRANSLATE_PROMPT

logger = logging.getLogger(__name__)

# Shared constants
_SYSTEM_ROLE = "You are a helpful academic research assistant."
_MARKDOWN_CODE_RE = re.compile(r'^```(?:json)?\s*|\s*```$', re.MULTILINE)
_CITATION_RE = re.compile(r"\[(\d+)\]")

# Truncation limits for LLM prompts
_ABSTRACT_MAX_LENGTH = 2000
_ABSTRACT_PREVIEW_LENGTH = 500
_PREVIOUS_ANSWER_MAX_LENGTH = 1000
_CROSS_PAPER_MAX_PAPERS = 5
_LOG_TITLE_PREVIEW_LENGTH = 50


@dataclass
class LLMResponse:
    """Represents a response from an LLM."""

    answer: str
    citations: List[int]  # List of paper indices referenced in the answer
    reasoning: Optional[str] = None
    error: Optional[str] = None


class LLMProcessor:
    """Processes papers using LLMs to generate summaries and answers."""

    # Token limits for specific operations (smaller than the default self.max_tokens)
    TRANSLATE_MAX_TOKENS = 200
    ANALYSIS_MAX_TOKENS = 500

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        max_tokens: int = 2000,
        temperature: float = 0.1,
        openai_api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
    ):
        """
        Initialize the LLM processor.

        Args:
            model: LLM model to use
            max_tokens: Maximum tokens for response
            temperature: Temperature for generation (lower = more factual)
            openai_api_key: OpenAI API key (falls back to env var if not provided)
            api_base_url: Custom API base URL for OpenAI-compatible APIs
        """
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.openai_api_key = openai_api_key
        self.api_base_url = (api_base_url.strip() or None) if isinstance(api_base_url, str) else None

        # Initialize OpenAI client (optional, can be done later)
        try:
            self.client = self._initialize_client()
        except ValueError:
            # No API key, but still allow initialization for paper search
            self.client = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_messages(self, user_content: str) -> list:
        """Build the standard message list used by all LLM calls."""
        return [
            {"role": "system", "content": _SYSTEM_ROLE},
            {"role": "user", "content": user_content},
        ]

    @staticmethod
    def _strip_markdown_codeblock(text: str) -> str:
        """Remove surrounding ```json … ``` fences from LLM output."""
        return _MARKDOWN_CODE_RE.sub("", text).strip()

    @staticmethod
    def _extract_citations(text: str, paper_count: int) -> List[int]:
        """Extract 0-based citation indices from [1], [2]… in *text*.

        Only returns indices that fall within [0, paper_count).
        """
        raw = {int(m) for m in _CITATION_RE.findall(text)}
        return sorted(c - 1 for c in raw if 0 < c <= paper_count)

    # ------------------------------------------------------------------
    # Client initialization
    # ------------------------------------------------------------------

    def _initialize_client(self):
        """Initialize the OpenAI client."""
        try:
            from openai import OpenAI

            api_key = self.openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY 环境变量未设置")
            env_base = os.getenv("API_BASE_URL", "").strip()
            base_url = self.api_base_url or (env_base if env_base else None)
            if base_url:
                return OpenAI(api_key=api_key, base_url=base_url)
            return OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("未安装 OpenAI 包。请使用 pip install openai 安装")

    def generate_answer(self, query: str, papers: List[Paper]) -> LLMResponse:
        """
        Generate an answer to a query based on the provided papers.

        Args:
            query: User's query
            papers: List of relevant papers

        Returns:
            LLMResponse with answer and citations
        """
        if not isinstance(query, str):
            return LLMResponse(
                answer="查询必须是字符串类型。", citations=[], error="Invalid query type"
            )

        if not isinstance(papers, list):
            return LLMResponse(
                answer="论文列表必须是列表类型。", citations=[], error="Invalid papers type"
            )

        if not papers:
            return LLMResponse(
                answer="未找到相关论文。", citations=[], error="未提供论文"
            )

        if not self.client:
            paper_list = "\n".join(
                f"[{i+1}] {paper.title} ({paper.year})" for i, paper in enumerate(papers)
            )
            return LLMResponse(
                answer=f"找到 {len(papers)} 篇相关论文，但缺少 LLM API 密钥无法生成总结。\n\n论文列表：\n{paper_list}",
                citations=[], error="No API key provided"
            )

        context = self._prepare_context(papers)
        prompt = self._create_prompt(query, context)

        try:
            response_text = self._call_openai(prompt)
            citations = self._extract_citations(response_text, len(papers))
            return LLMResponse(answer=response_text, citations=citations)

        except Exception as e:
            logger.error("Error generating answer: %s", e)
            return LLMResponse(
                answer="生成答案时遇到错误。", citations=[], error=str(e),
            )

    def analyze_single_paper(self, paper: Paper) -> PaperAnalysis:
        """
        Extract structured analysis from a single paper.

        Args:
            paper: The paper to analyze

        Returns:
            PaperAnalysis with extracted information
        """
        if not self.client:
            return PaperAnalysis()

        try:
            prompt = ANALYSIS_PROMPT.format(
                title=paper.title,
                abstract=paper.abstract[:_ABSTRACT_MAX_LENGTH] if paper.abstract else "无摘要"
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._make_messages(prompt),
                max_tokens=self.ANALYSIS_MAX_TOKENS,
                temperature=0.1,
            )

            result_text = self._strip_markdown_codeblock(
                response.choices[0].message.content
            )
            analysis_data = json.loads(result_text)

            return PaperAnalysis(
                keywords=analysis_data.get("keywords", []),
                research_method=analysis_data.get("research_method"),
                limitations=analysis_data.get("limitations"),
                contributions=analysis_data.get("contributions"),
            )

        except Exception as e:
            logger.warning("Error analyzing paper '%s': %s", paper.title[:_LOG_TITLE_PREVIEW_LENGTH], e)
            return PaperAnalysis()

    def cross_paper_analysis(self, query: str, papers: List[Paper]) -> CrossPaperAnalysis:
        """
        Perform comprehensive cross-paper analysis.

        Args:
            query: The original user query
            papers: List of papers to analyze

        Returns:
            CrossPaperAnalysis with comprehensive insights
        """
        if not self.client:
            return CrossPaperAnalysis(
                research_trends="需要API密钥才能进行分析",
                methodology_comparison="",
                research_gaps="",
                future_directions="",
            )

        if not papers:
            return CrossPaperAnalysis(
                research_trends="未找到相关论文",
                methodology_comparison="",
                research_gaps="",
                future_directions="",
            )

        context = self._prepare_context(papers)

        try:
            prompt = CROSS_PAPER_PROMPT.format(context=context, query=query)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._make_messages(prompt),
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            analysis_text = response.choices[0].message.content

            paper_analyses = []
            for paper in papers[:_CROSS_PAPER_MAX_PAPERS]:
                analysis = self.analyze_single_paper(paper)
                paper_analyses.append(analysis)

            return CrossPaperAnalysis(
                research_trends=self._extract_section(analysis_text, "研究趋势"),
                methodology_comparison=self._extract_section(analysis_text, "方法论对比"),
                research_gaps=self._extract_section(analysis_text, "研究空白"),
                future_directions=self._extract_section(analysis_text, "未来研究方向"),
                key_findings=self._extract_key_findings(analysis_text),
                paper_analyses=paper_analyses,
            )

        except Exception as e:
            logger.error("Error in cross-paper analysis: %s", e)
            return CrossPaperAnalysis(
                research_trends=f"分析过程中遇到错误：{str(e)}",
                methodology_comparison="",
                research_gaps="",
                future_directions="",
            )

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a section from the analysis text using robust multi-pattern matching."""
        patterns = [
            # Pattern 1: section header followed by content until next numbered section or end
            rf"###?\s*{section_name}[:：]?\s*\n(.*?)(?=\n###?\s*\d+\.|\n###?\s*未来研究方向|\n###?\s*关键发现|$)",
            # Pattern 2: numbered header with section name
            rf"\d+\.\s*{section_name}[:：]?\s*\n(.*?)(?=\n\d+\.|\n未来研究方向|\n关键发现|$)",
            # Pattern 3: simple colon-separated header
            rf"{section_name}[:：]\s*\n(.*?)(?=\n[A-Z]|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                section_text = match.group(1).strip()
                section_text = re.sub(r'\n{3,}', '\n\n', section_text)
                if section_text:
                    return section_text

        # Fallback: return empty string instead of the entire text
        return ""

    def _extract_key_findings(self, text: str) -> List[str]:
        """Extract key findings as a list."""

        findings_pattern = r"关键发现[:：]?\s*\n?(.*?)(?=\n未来|$)"
        match = re.search(findings_pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            findings_text = match.group(1)
            findings = re.findall(r'[-•\d]\s*(.+)', findings_text)
            if findings:
                return [f.strip() for f in findings if f.strip()]

        return []

    def handle_followup(self, followup_query: str, papers: List[Paper],
                       previous_answer: str = "") -> LLMResponse:
        """
        Handle follow-up questions about search results.

        Args:
            followup_query: User's follow-up question
            papers: List of papers from original search
            previous_answer: Previous answer to maintain context

        Returns:
            LLMResponse with answer and citations
        """
        if not self.client:
            return LLMResponse(
                answer="需要API密钥才能进行追问。",
                citations=[],
                error="No API key provided"
            )

        if not papers:
            return LLMResponse(
                answer="没有可用的论文信息来回答你的问题。",
                citations=[],
                error="No papers available"
            )

        context = self._prepare_context(papers)

        try:
            prompt = FOLLOWUP_PROMPT.format(
                previous_answer=previous_answer[:_PREVIOUS_ANSWER_MAX_LENGTH] if previous_answer else "无",
                context=context,
                followup_query=followup_query
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._make_messages(prompt),
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            answer_text = response.choices[0].message.content
            citations = self._extract_citations(answer_text, len(papers))

            return LLMResponse(answer=answer_text, citations=citations)

        except Exception as e:
            logger.error("Error handling follow-up: %s", e)
            return LLMResponse(
                answer=f"处理追问时遇到错误：{str(e)}",
                citations=[],
                error=str(e),
            )

    def _prepare_context(self, papers: List[Paper]) -> str:
        """Prepare context string from papers."""
        parts = []
        for i, paper in enumerate(papers, 1):
            lines = [
                f"[{i}] {paper.title}",
                f"   Authors: {format_author_names(paper.authors, max_shown=3)}",
            ]
            if paper.year:
                lines.append(f"   Year: {paper.year}")
            if paper.venue:
                lines.append(f"   Venue: {paper.venue}")
            if paper.abstract:
                abstract = paper.abstract[:_ABSTRACT_PREVIEW_LENGTH - 3] + "..." if len(paper.abstract) > _ABSTRACT_PREVIEW_LENGTH else paper.abstract
                lines.append(f"   Abstract: {abstract}")
            parts.append("\n".join(lines))
        return "\n".join(parts)

    def _create_prompt(self, query: str, context: str) -> str:
        """Create the prompt for the LLM."""
        return ANSWER_PROMPT.format(context=context, query=query)

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._make_messages(prompt),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return response.choices[0].message.content

    def translate_query(self, query: str, target_language: str = "English") -> str:
        """
        Translate a user query to a more formal, academic search query.

        Args:
            query: User's original query
            target_language: Target language for the translated query ("English" or "Chinese")

        Returns:
            Translated query suitable for academic paper search
        """
        if not self.client:
            return query

        prompt = TRANSLATE_PROMPT.format(query=query, target_language=target_language)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._make_messages(prompt),
                max_tokens=self.TRANSLATE_MAX_TOKENS,
                temperature=self.temperature,
            )

            translated_query = response.choices[0].message.content.strip()
            logger.info("Translated query from '%s' to '%s'", query, translated_query)
            return translated_query

        except Exception as e:
            logger.warning("Error translating query: %s", e)
            return query

