import os
import re
import logging
from typing import List, Optional
from dataclasses import dataclass

from ..models.paper import Paper, format_author_names

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Represents a response from an LLM."""

    answer: str
    citations: List[int]  # List of paper indices referenced in the answer
    reasoning: Optional[str] = None
    error: Optional[str] = None


class LLMProcessor:
    """Processes papers using LLMs to generate summaries and answers."""

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
        if isinstance(api_base_url, str):
            s = api_base_url.strip()
            self.api_base_url = s if s else None
        else:
            self.api_base_url = None

        # Initialize OpenAI client
        self.client = self._initialize_client()

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
        # Validate input types
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

        # Prepare context from papers
        context = self._prepare_context(papers)

        # Generate prompt
        prompt = self._create_prompt(query, context, papers)

        try:
            response = self._call_openai(prompt)

            # Parse response to extract citations
            answer, citations = self._parse_response(response)

            return LLMResponse(answer=answer, citations=citations, reasoning=None)

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return LLMResponse(
                answer="生成答案时遇到错误。",
                citations=[],
                error=str(e),
            )

    def _prepare_context(self, papers: List[Paper]) -> str:
        """Prepare context string from papers."""
        context_parts = []

        for i, paper in enumerate(papers, 1):
            authors_str = format_author_names(paper.authors, max_shown=3)

            # Create paper entry
            paper_entry = f"[{i}] {paper.title}\n"
            paper_entry += f"   Authors: {authors_str}\n"
            if paper.year:
                paper_entry += f"   Year: {paper.year}\n"
            if paper.venue:
                paper_entry += f"   Venue: {paper.venue}\n"
            if paper.abstract:
                # Truncate abstract if too long
                abstract = paper.abstract
                if len(abstract) > 500:
                    abstract = abstract[:497] + "..."
                paper_entry += f"   Abstract: {abstract}\n"

            context_parts.append(paper_entry)

        return "\n".join(context_parts)

    def _create_prompt(self, query: str, context: str, papers: List[Paper]) -> str:
        """Create the prompt for the LLM."""
        system_prompt = """\
You are an AI academic research assistant. \
Your task is to answer questions based ONLY on the provided academic papers.

CRITICAL INSTRUCTIONS:
1. BASE YOUR ANSWER STRICTLY ON THE PROVIDED PAPERS. Do not use any external knowledge.
2. Every claim you make MUST be supported by a citation to one or more of the provided papers.
3. Use citation format [1], [2], etc. where the number corresponds to the paper number in the provided list.
4. If the papers don't contain information to answer the question, say so explicitly.
5. Do not invent or hallucinate any information about papers, authors, or findings.
6. Be concise but comprehensive in your answer.

Format your answer as follows:
1. Start with a direct answer to the query.
2. Provide supporting evidence with citations.
3. Summarize key findings from relevant papers.
4. End with a conclusion.

Papers:
{context}

Query: {query}

Answer:"""

        return system_prompt.format(context=context, query=query)

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful academic research assistant.",
            },
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        return response.choices[0].message.content

    def _parse_response(self, response: str) -> tuple:
        """Parse LLM response to extract answer and citations."""
        # Extract citations (numbers in brackets)
        citation_pattern = r"\[(\d+)\]"
        citations = list(
            set(int(match) for match in re.findall(citation_pattern, response))
        )

        # Convert to 0-based indices for internal use
        citations = [c - 1 for c in citations if 0 < c <= 100]  # Reasonable upper bound

        return response, citations

    def summarize_paper(self, paper: Paper) -> str:
        """Generate a concise summary of a single paper."""
        prompt = f"""Please provide a concise summary of the following academic paper:

Title: {paper.title}
Authors: {', '.join([author.name for author in paper.authors[:3]])}
Year: {paper.year or 'Unknown'}
Abstract: {paper.abstract or 'No abstract available'}

Provide a 2-3 sentence summary focusing on:
1. The main research question or objective
2. Key findings or contributions
3. Methodology (if mentioned in abstract)

Summary:"""

        try:
            return self._call_openai(prompt)
        except Exception as e:
            logger.error(f"Error summarizing paper: {e}")
            return f"Summary unavailable: {str(e)}"
