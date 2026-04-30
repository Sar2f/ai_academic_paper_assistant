from typing import Tuple, Optional

from ..llm.processor import LLMProcessor
from ..utils.validation import normalize_search_query


class QueryProcessor:
    """处理查询预处理和翻译"""

    def __init__(self, llm_processor: LLMProcessor):
        self.llm_processor = llm_processor

    def validate_and_normalize(self, query: str) -> Tuple[bool, str, Optional[str]]:
        """
        验证并规范化查询

        Returns:
            (is_valid, normalized_query, error_message)
        """
        if not isinstance(query, str):
            return False, "", "查询必须是字符串类型"

        normalized = normalize_search_query(query)
        if not normalized:
            return False, "", "请输入有效的检索内容"

        return True, normalized, None

    def translate_query(self, query: str) -> str:
        """
        将查询翻译为英文学术搜索用语。

        Chinese queries get a single LLM call to translate to English.
        English queries get an LLM call to formalise into academic English.
        No LLM available returns the original query.

        Returns:
            English academic search query string
        """
        if not self.llm_processor.client:
            return query

        return self.llm_processor.translate_query(query, target_language="English")
