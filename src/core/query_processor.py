from typing import Dict, Optional, Tuple

from ..llm.processor import LLMProcessor
from ..utils.validation import normalize_search_query


class QueryProcessor:
    """Validates, normalizes, and translates user queries for academic search."""

    def __init__(self, llm_processor: LLMProcessor):
        self.llm_processor = llm_processor

    def validate_and_normalize(self, query: str) -> Tuple[bool, str, Optional[str]]:
        """Validate and normalize a user query.

        Returns:
            (is_valid, normalized_query, error_message)
        """
        if not isinstance(query, str):
            return False, "", "Query must be a string"
        normalized = normalize_search_query(query)
        if not normalized:
            return False, "", "Please enter a valid search query"
        return True, normalized, None

    def translate_query(self, query: str) -> Dict[str, str]:
        """Translate query for different API targets.

        Returns:
            {"original": str, "english": str, "chinese": str}
        """
        is_chinese = any('一' <= char <= '鿿' for char in query)

        if is_chinese:
            english_query = self.llm_processor.translate_query(query, target_language="English")
            return {"original": query, "english": english_query, "chinese": query}
        else:
            return {"original": query, "english": query, "chinese": query}

