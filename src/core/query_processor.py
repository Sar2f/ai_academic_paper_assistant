from typing import Tuple, Optional, Dict

from ..llm.processor import LLMProcessor
from ..utils.validation import normalize_search_query


class QueryProcessor:
    """处理查询预处理和翻译"""

    def __init__(self, llm_processor: LLMProcessor):
        """
        初始化查询处理器

        Args:
            llm_processor: LLM处理器实例
        """
        self.llm_processor = llm_processor

    def validate_and_normalize(self, query: str) -> Tuple[bool, str, Optional[str]]:
        """
        验证并规范化查询

        Args:
            query: 用户查询

        Returns:
            (is_valid, normalized_query, error_message)
        """
        if not isinstance(query, str):
            return False, "", "查询必须是字符串类型"

        normalized = normalize_search_query(query)
        if not normalized:
            return False, "", "请输入有效的检索内容"

        return True, normalized, None

    def translate_query(self, query: str) -> Dict[str, str]:
        """
        翻译查询为适合不同API的格式

        Uses a single LLM call to produce both English and Chinese
        translations simultaneously, avoiding double API calls.

        Args:
            query: 已规范化的查询

        Returns:
            {
                "original": str,  # 原始查询
                "english": str,   # 英文查询（用于大多数API）
                "chinese": str    # 中文查询（用于中文API）
            }
        """
        is_chinese = any('\u4e00' <= char <= '\u9fff' for char in query)

        if not self.llm_processor.client:
            # No LLM available — return original for both
            return {"original": query, "english": query, "chinese": query}

        # Single LLM call for both translations
        if is_chinese:
            english_query = self.llm_processor.translate_query(query, target_language="English")
            # For Chinese queries, the "Chinese" version is the original (already Chinese)
            chinese_query = query
        else:
            # For English queries, translate to academic English and also get Chinese
            english_query = self.llm_processor.translate_query(query, target_language="English")
            chinese_query = english_query  # Same query works for both

        return {
            "original": query,
            "english": english_query,
            "chinese": chinese_query,
        }
