# AI Academic Paper Assistant — Repository Memory

## Architecture Overview

- **BaseAPI pattern**: All API clients inherit from `BaseAPI` and only implement
  `_build_connection_test()` and `_fetch_raw()`. Retry logic, query normalization,
  and rate limiting are handled by the base class via `search_papers()` and
  `_search_with_retry()`.
- **API_NAME**: Each API subclass declares `API_NAME` (used in logs and status dicts).
- **API Manager**: Uses `ThreadPoolExecutor` for concurrent API searches and
  `_normalise_title()` for fuzzy deduplication (case + whitespace + punctuation).
- **LLM Processor**: Uses `self.max_tokens` (not hardcoded). `_extract_section()`
  returns empty string on failure (not the whole text). All imports are at the top.
- **QueryProcessor**: Single LLM call for Chinese→English translation; Chinese queries
  don't call `translate_query("Chinese")` redundantly.

## Key Commands

- **Run unit tests**: `pytest tests/api/test_base_api.py tests/integration/test_integration.py -v`
- **Run app**: `streamlit run app.py --server.port 8501 --server.address 0.0.0.0`
- **Install deps**: `pip install -r requirements.txt`

## Code Patterns

- BaseAPI subclass: implement `_build_connection_test()` → returns `(url, params, timeout)`
  and `_fetch_raw()` → returns `SearchResult` (must raise HTTPError on failure for retry).
- Title dedup: `_normalise_title()` strips punctuation, lowercases, collapses whitespace.
- Config validation: `AppConfig.validate()` raises `ValueError` on invalid settings.
- Orchestrator `validate_configuration()`: checks key existence only, no real LLM API call.

## Things to Avoid

- Never add retry logic in API subclasses — it's in `BaseAPI._search_with_retry()`.
- Never return the entire analysis text from `_extract_section()` on failure — return `""`.
- Never hardcode `max_tokens` in LLM calls — use `self.max_tokens`.
- Never duplicate `import json` / `import re` inside methods — they're at the top.

## Recent Optimizations (2026-04-30)

1. **BaseAPI refactoring**: Eliminated ~200 lines of duplicated retry/connection
   logic across 4 API subclasses by moving it to BaseAPI.
2. **Concurrent search**: API Manager now uses ThreadPoolExecutor for parallel API
   searches instead of sequential iteration.
3. **Fuzzy dedup**: Title normalization (case + punctuation + whitespace) for better
   cross-API deduplication. Keeps richer metadata version on collision.
4. **LLM Processor cleanup**: Moved `import json/re` to top; fixed `_extract_section`
   regex to be more robust (returns `""` on failure); used `self.max_tokens` instead
   of hardcoded 2000.
5. **QueryProcessor optimization**: Chinese queries now only call LLM once for
   English translation (instead of twice for both English and Chinese).
6. **Orchestrator cleanup**: Removed wasteful LLM API call in `validate_configuration()`.
7. **Config validation**: Clarified docstring: "Raises ValueError on invalid settings".
8. **Test fixes**: Fixed broken `_create_prompt(query, context, papers)` → `_create_prompt(query, context)`.
   Added `test_processor_without_api_key` test. Added `test_base_api.py` with 11 tests.