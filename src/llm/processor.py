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

        # Initialize OpenAI client (optional, can be done later)
        try:
            self.client = self._initialize_client()
        except ValueError:
            # No API key, but still allow initialization for paper search
            self.client = None

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

        # Check if client is initialized
        if not self.client:
            # No API key, return paper list without LLM answer
            paper_list = "\n".join([f"[{i+1}] {paper.title} ({paper.year})" for i, paper in enumerate(papers)])
            return LLMResponse(
                answer=f"找到 {len(papers)} 篇相关论文，但缺少 LLM API 密钥无法生成总结。\n\n论文列表：\n{paper_list}",
                citations=[],
                error="No API key provided"
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
            logger.error("Error generating answer: %s", e)
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

    def _create_prompt(self, query: str, context: str, _papers: List[Paper]) -> str:
        """Create the prompt for the LLM."""
        system_prompt = """\
你是一个 AI 学术研究助手。\
你的任务是仅基于提供的学术论文回答问题。

重要指示：
1. 严格基于提供的论文回答问题，不要使用任何外部知识。
2. 你提出的每一个主张都必须有一个或多个提供的论文的引用支持。
3. 使用引用格式 [1], [2] 等，其中数字对应于提供列表中的论文编号。
4. 如果论文中不包含回答问题的信息，请明确说明。
5. 不要编造或幻觉任何关于论文、作者或发现的信息。
6. 回答要简洁但全面。

请用中文回答问题，回答格式如下：
1. 以对查询的直接回答开始。
2. 提供带有引用的支持证据。
3. 总结相关论文的关键发现。
4. 以结论结束。

论文：
{context}

查询：{query}

回答："""

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
            # No API key, return original query
            return query

        system_prompt = """
你是一个学术搜索助手，负责将用户的日常口语查询转换为正式的学术搜索查询。

请将以下用户查询转换为更正式、更适合学术论文搜索的查询语句：
1. 如果用户使用中文，将其转换为正式的中文学术用语
2. 如果目标语言是英文，将其翻译为正式的英文学术用语
3. 保持查询的核心含义不变
4. 尽量使用学术领域的专业术语
5. 输出简洁明了的查询语句，不要添加任何解释

用户查询：{query}
目标语言：{target_language}

转换后的查询：
"""

        prompt = system_prompt.format(query=query, target_language=target_language)

        try:
            messages = [
                {"role": "system", "content": "You are a helpful academic research assistant."},
                {"role": "user", "content": prompt},
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.1,
            )

            translated_query = response.choices[0].message.content.strip()
            logger.info(f"Translated query from '{query}' to '{translated_query}'")
            return translated_query

        except Exception as e:
            logger.warning("Error translating query: %s", e)
            return query


