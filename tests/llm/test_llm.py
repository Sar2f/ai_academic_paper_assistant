"""Tests for LLMProcessor internals: _extract_section, _extract_key_findings, _strip_markdown_codeblock."""

import os
import pytest

from src.llm.processor import LLMProcessor


class TestExtractSection:
    """Tests for _extract_section."""

    @pytest.fixture
    def processor(self):
        original_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            proc = LLMProcessor(openai_api_key=None)
            assert proc.client is None
            return proc
        finally:
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key

    def test_extract_section_markdown_header(self, processor):
        text = "### 研究趋势：\nAI is growing.\n\n### 2. 方法论对比：\nSome methods."
        result = processor._extract_section(text, "研究趋势")
        assert "AI is growing" in result

    def test_extract_section_numbered_header(self, processor):
        text = "1. 研究趋势：\nAI is growing.\n\n2. 方法论对比：\nSome methods."
        result = processor._extract_section(text, "研究趋势")
        assert "AI is growing" in result

    def test_extract_section_not_found_returns_empty(self, processor):
        text = "Some random text without any section headers."
        result = processor._extract_section(text, "研究趋势")
        assert result == ""

    def test_extract_key_findings(self, processor):
        text = "关键发现：\n- Finding one\n- Finding two\n\n未来研究方向：\nSomething."
        result = processor._extract_key_findings(text)
        assert len(result) == 2
        assert "Finding one" in result[0]

    def test_extract_key_findings_empty(self, processor):
        text = "No findings here."
        result = processor._extract_key_findings(text)
        assert result == []

    def test_strip_markdown_codeblock(self):
        text = '```json\n{"key": "value"}\n```'
        result = LLMProcessor._strip_markdown_codeblock(text)
        assert result == '{"key": "value"}'

    def test_strip_markdown_codeblock_plain(self):
        text = '{"key": "value"}'
        result = LLMProcessor._strip_markdown_codeblock(text)
        assert result == '{"key": "value"}'

    def test_extract_citations(self):
        text = "According to [1] and [3]."
        result = LLMProcessor._extract_citations(text, 5)
        assert result == [0, 2]

    def test_extract_citations_out_of_range(self):
        text = "According to [1] and [10]."
        result = LLMProcessor._extract_citations(text, 5)
        assert result == [0]  # [10] is out of range (paper_count=5)

    def test_extract_citations_no_citations(self):
        text = "No citations here."
        result = LLMProcessor._extract_citations(text, 5)
        assert result == []


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_detect_default_source(self):
        from src.utils.config_manager import ConfigManager
        manager = ConfigManager(config_dir="/nonexistent")
        source = manager.detect_config_source()
        assert source == "default"

    def test_load_default_config(self):
        from src.utils.config_manager import ConfigManager
        manager = ConfigManager(config_dir="/nonexistent")
        config = manager.load_config("default")
        assert config.llm_model == "gpt-4o-mini"

    def test_load_env_config(self):
        import os
        from src.utils.config_manager import ConfigManager
        os.environ["MAX_PAPERS_TO_RETRIEVE"] = "5"
        try:
            manager = ConfigManager(config_dir="/nonexistent")
            config = manager.load_config("env")
            assert config.max_papers_to_retrieve == 5
        finally:
            del os.environ["MAX_PAPERS_TO_RETRIEVE"]


class TestTranslator:
    """Tests for Translator."""

    def test_translate_en(self):
        from src.i18n.translations import Translator
        t = Translator("en")
        assert t.t("app_title") == "📚 AI Academic Paper Assistant"

    def test_translate_zh(self):
        from src.i18n.translations import Translator
        t = Translator("zh")
        assert t.t("app_title") == "📚 AI 学术论文助手"

    def test_translate_with_kwargs(self):
        from src.i18n.translations import Translator
        t = Translator("en")
        result = t.t("results_found", count=5)
        assert "5" in result

    def test_translate_missing_key_falls_back(self):
        from src.i18n.translations import Translator
        t = Translator("zh")
        result = t.t("nonexistent_key")
        assert result == "nonexistent_key"

    def test_set_language(self):
        from src.i18n.translations import Translator
        t = Translator("en")
        t.set_language("zh")
        assert t.language == "zh"

    def test_set_language_invalid_defaults_en(self):
        from src.i18n.translations import Translator
        t = Translator("en")
        t.set_language("invalid")
        assert t.language == "en"