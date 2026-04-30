import json
import os
import re
import logging
from typing import List, Optional
from dataclasses import dataclass

from ..models.paper import Paper, format_author_names, PaperAnalysis, CrossPaperAnalysis

logger = logging.getLogger(__name__)

# Shared constants
_SYSTEM_ROLE = "You are a helpful academic research assistant."
_MARKDOWN_CODE_RE = re.compile(r'^```(?:json)?\s*|\s*```$', re.MULTILINE)
_CITATION_RE = re.compile(r"\[(\d+)\]")


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

        system_prompt = """你是一个学术论文分析助手。请从以下论文中提取结构化信息。

请用JSON格式返回，字段如下：
- keywords: 3-5个核心关键词列表
- research_method: 研究方法（如：实证研究、理论分析、综述、案例研究、实验等）
- limitations: 主要研究局限性（1-2句话）
- contributions: 主要贡献（1-2句话）

论文信息：
标题：{title}
摘要：{abstract}

请仅返回JSON，不要有其他内容。"""

        try:
            prompt = system_prompt.format(
                title=paper.title,
                abstract=paper.abstract[:2000] if paper.abstract else "无摘要"
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
            logger.warning("Error analyzing paper '%s': %s", paper.title[:50], e)
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

        system_prompt = """你是一个AI学术研究助手，负责对一组相关论文进行跨论文综合分析。

请基于提供的论文集合，进行以下分析：

1. **研究趋势（Research Trends）**：
   - 该领域近年的发展趋势
   - 研究热点的演变
   - 技术或方法的进步

2. **方法论对比（Methodology Comparison）**：
   - 不同论文采用的主要研究方法
   - 各方法的优缺点
   - 方法选择的依据

3. **研究空白（Research Gaps）**：
   - 当前研究中的不足或未被解决的问题
   - 理论或实践中的gap
   - 不同研究结论矛盾的地方

4. **未来研究方向（Future Directions）**：
   - 基于现有研究的未来研究建议
   - 可能的研究突破口
   - 值得探索的新领域

5. **关键发现（Key Findings）**：
   - 列出3-5个最重要的研究发现

请用中文详细回答以上各个方面。

论文列表：
{context}

查询：{query}

分析结果："""

        try:
            prompt = system_prompt.format(context=context, query=query)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._make_messages(prompt),
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            analysis_text = response.choices[0].message.content

            paper_analyses = []
            for paper in papers[:5]:
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

        system_prompt = """\
你是一个AI学术研究助手，专门处理用户的追问。

用户之前搜索了相关论文并获得了回答，现在他们提出了一个跟进问题。

请遵循以下指示：
1. 严格基于提供的论文回答问题，不要使用任何外部知识。
2. 如果用户要求"找到类似论文"，请分析现有论文的主题，建议搜索方向。
3. 如果用户询问某篇论文的细节，请深入分析该论文的内容。
4. 如果用户询问研究方法的具体细节，请基于论文中的方法部分进行解释。
5. 使用引用格式 [1], [2] 等，其中数字对应于提供列表中的论文编号。
6. 如果论文中不包含回答问题的信息，请明确说明。

之前的回答（供参考）：
{previous_answer}

论文列表：
{context}

追问：{followup_query}

回答："""

        try:
            prompt = system_prompt.format(
                previous_answer=previous_answer[:1000] if previous_answer else "无",
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
                abstract = paper.abstract[:497] + "..." if len(paper.abstract) > 500 else paper.abstract
                lines.append(f"   Abstract: {abstract}")
            parts.append("\n".join(lines))
        return "\n".join(parts)

    def _create_prompt(self, query: str, context: str) -> str:
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


