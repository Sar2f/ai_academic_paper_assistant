# AI Academic Paper Assistant — Repository Memory

## Architecture Overview

- **BaseAPI pattern**: All API clients inherit from `BaseAPI` and only implement
  `_build_connection_test()` and `_fetch_raw()`. Retry logic, query normalization,
  and rate limiting are handled by the base class via `search_papers()` and
  `_search_with_retry()`.
- **API_NAME**: Each API subclass declares `API_NAME` (used in logs and status dicts).
- **API Manager**: Uses `ThreadPoolExecutor` for concurrent API searches and
  `_normalise_title()` for fuzzy deduplication (case + whitespace + punctuation).
- **LLM Processor**: Uses `self.max_tokens` and `self.temperature` (not hardcoded).
  Helper methods: `_make_messages()`, `_extract_citations()`, `_strip_markdown_codeblock()`.
  Class-level token constants: `TRANSLATE_MAX_TOKENS=200`, `ANALYSIS_MAX_TOKENS=500`.
  `_extract_section()` returns empty string on failure (not the whole text).
- **QueryProcessor**: `translate_query()` returns a single English academic search string
  (not a dict). Chinese queries get English translation; English queries get formalised
  academic English. No Chinese translation is generated (unused by pipeline).
- **FallbackHandler**: Uses shared `_deduplicate_papers()` from `api_manager` module.

## Key Commands

- **Run unit tests**: `pytest tests/api/test_base_api.py tests/integration/test_integration.py -v`
- **Run app**: `streamlit run app.py --server.port 8501 --server.address 0.0.0.0`
- **Install deps**: `pip install -r requirements.txt`

## Code Patterns

- BaseAPI subclass: implement `_build_connection_test()` → returns `(url, params, timeout)`
  and `_fetch_raw()` → returns `SearchResult` (must raise HTTPError on failure for retry).
- Title dedup: `_deduplicate_papers(papers, limit)` — shared function in `api_manager`
  module, used by both `APIManager.search_all_apis()` and `FallbackHandler.try_fallback_apis()`.
  Internally uses `_normalise_title()` which strips punctuation, lowercases, collapses whitespace.
- Config validation: `AppConfig.validate()` raises `ValueError` on invalid settings.
- Orchestrator `validate_configuration()`: checks `self.llm_processor.client` (not `self.client`).
- LLM calls all use `self._make_messages(prompt)` for consistent system role.
- Citation extraction: `_extract_citations(text, paper_count)` — uses `paper_count`
  to bound indices, not a hardcoded magic number.
- Logger calls: use `%s` lazy formatting, not f-strings.
- `min_citation_count` checks: use `is not None` (truthy check skips 0).

## Things to Avoid

- Never add retry logic in API subclasses — it's in `BaseAPI._search_with_retry()`.
- Never return the entire analysis text from `_extract_section()` on failure — return `""`.
- Never hardcode `max_tokens` or `temperature` in LLM calls — use class constants or `self.*`.
- Never duplicate `import json` / `import re` inside methods — they're at the top.
- Never reference `self.client` in Orchestrator — it's `self.llm_processor.client`.
- Never use `if min_citation_count:` — use `if min_citation_count is not None:`.
- Never use f-strings in logger calls — use `%s` lazy formatting.

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

## Code Quality Review (2026-04-30)

### Bug Fixes

1. **orchestrator.validate_configuration()**: Fixed `self.client` → `self.llm_processor.client`
   (was referencing nonexistent attribute, would crash on call).
2. **query_processor.translate_query()**: Fixed non-Chinese queries — English queries now
   get a separate Chinese translation instead of using the English query as "Chinese".
3. **openalex_api._fetch_raw()**: Fixed `if min_citation_count:` → `if min_citation_count is not None:`
   (truthy check incorrectly skipped min_citation_count=0).
4. **fallback_handler.try_fallback_apis()**: Added title-based deduplication (was missing,
   unlike APIManager.search_all_apis() which already had it).
5. **LLMProcessor**: Fixed hardcoded `max_tokens=200` in translate_query → `TRANSLATE_MAX_TOKENS`;
   hardcoded `max_tokens=500` in analyze_single_paper → `ANALYSIS_MAX_TOKENS`;
   hardcoded `temperature=0.1` in cross_paper_analysis → `self.temperature`.
6. **_parse_response()**: Fixed magic number `100` as citation upper bound → uses `paper_count`
   from `_extract_citations(text, paper_count)`.
7. **Logger f-strings**: Fixed in api_manager.py and llm/processor.py — use `%s` lazy formatting.

### Redundancy Elimination

1. **System role**: Extracted `_SYSTEM_ROLE` constant + `_make_messages()` helper —
   replaced 5 duplicate `{"role": "system", ...}` dicts.
2. **Citation parsing**: Extracted `_extract_citations()` static method —
   replaced duplicate logic in `_parse_response()` and `handle_followup()`.
3. **Markdown code block stripping**: Extracted `_strip_markdown_codeblock()` with
   compiled `_MARKDOWN_CODE_RE` — replaced 3 separate `re.sub()` calls.
4. **Sidebar connection status**: Replaced 4 copy-pasted API status blocks with a loop.
5. **Removed `_parse_response()` method** — citation extraction now inline via helper.

### Code Simplification

1. **LLMProcessor.__init__**: Simplified `api_base_url` initialization (one-liner ternary).
2. **LLMProcessor._prepare_context**: Simplified string building with list-of-lines pattern.
3. **display_cross_paper_analysis**: Simplified truncation pattern with `_truncate` lambda.
4. **Cleaned trailing/extra blank lines** across multiple files.

## Audit & Cleanup (2026-04-30, Round 2)

### Bug Fixes

1. **orchestrator.process_query()**: Fixed `translated_queries` NameError in except block —
   if exception occurred before `translate_query()` was called, the variable was undefined.
   Now uses `normalized_query` directly in the fallback path.
2. **orchestrator.py logger f-strings**: Fixed 3 remaining logger f-strings → `%s` lazy formatting.

### Dead Code Removal

1. **Removed unused imports**: `asdict` from `config_manager.py`, `Dict`/`Any` from `config_manager.py`.
2. **Removed `get_available_models()`**: Never called anywhere in the codebase.
3. **Removed `_load_from_env()` wrapper**: One-line `AppConfig.from_env()` call in `ConfigManager`.
4. **Removed `project_memory.json`**: Empty file, never used.
5. **Removed 13 script-style test files**: They were manual run scripts with `if __name__`,
   not proper pytest tests. Kept only `test_base_api.py` and `test_integration.py`.

### Redundancy Elimination

1. **Extracted `_deduplicate_papers()`**: Shared dedup logic used by both `APIManager` and
   `FallbackHandler`, replacing 12 lines of duplicated code in each.
2. **Simplified `QueryProcessor.translate_query()`**: Returns `str` instead of `Dict[str, str]`.
   Removed unused Chinese translation for English queries (was never consumed by pipeline,
   wasted one LLM API call per English query).

### Cleanup

1. **Fixed `.gitignore`**: Removed duplicate entries (`.DS_Store`, `.env.local`), added `.trae/`.
2. **Unified import style**: `streamlit_components.py` changed from absolute to relative imports.
3. **Removed redundant lazy import**: `app.py` no longer inline-imports `Translator` in
   session_state init block (it's already imported at top level).
4. **Fixed `app.py` docstring**: Removed reference to non-existent `src/ui` directory.