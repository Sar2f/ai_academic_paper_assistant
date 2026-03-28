"""
Input validation for search and retrieval (defensive defaults for demos and grading).
"""

from __future__ import annotations

from typing import Optional

# Reasonable bounds for a thesis demo / public API
MAX_QUERY_LENGTH = 2000
MIN_PAPERS = 1
MAX_PAPERS = 50
# UI number_input max (aligned with app.py)
MAX_PAPERS_UI = 20


def normalize_search_query(raw: Optional[str]) -> Optional[str]:
    """
    Strip whitespace; reject empty or over-long queries.

    Returns None if the query should be rejected before calling external APIs.
    """
    if raw is None:
        return None
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if not text:
        return None
    if len(text) > MAX_QUERY_LENGTH:
        return text[:MAX_QUERY_LENGTH]
    return text


def clamp_paper_limit(value: Optional[int], fallback: int, cap: int = MAX_PAPERS_UI) -> int:
    """Clamp paper count to [MIN_PAPERS, min(cap, MAX_PAPERS)]."""
    try:
        n = int(value if value is not None else fallback)
    except (TypeError, ValueError):
        n = int(fallback)
    upper = min(cap, MAX_PAPERS)
    return max(MIN_PAPERS, min(n, upper))
