"""
Streamlit layout and widgets. No retrieval or LLM calls here.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional, Tuple

import streamlit as st

from src.core.orchestrator import AcademicPaperOrchestrator
from src.i18n.translations import Translator
from src.models.paper import Paper, format_author_names
from src.utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)

APP_CSS = """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 2rem;
    }
    .paper-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3B82F6;
        background-color: #F8FAFC;
        margin-bottom: 1rem;
    }
    .citation {
        background-color: #EFF6FF;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
        color: #1D4ED8;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        margin-bottom: 1rem;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        margin-bottom: 1rem;
    }
    .answer-container {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
</style>
"""


def get_translator() -> Translator:
    if "translator" not in st.session_state:
        st.session_state.translator = Translator(st.session_state.get("current_language", "zh"))
    return st.session_state.translator


def initialize_app(config_source: Optional[str] = None) -> bool:
    """Load config and wire orchestrator into session state."""
    try:
        config_manager: ConfigManager = st.session_state.config_manager
        config = config_manager.load_config(config_source)
        orchestrator = AcademicPaperOrchestrator(config)
        st.session_state.config = config
        st.session_state.orchestrator = orchestrator
        logger.info(
            "Application initialized successfully from %s",
            config_manager.current_source,
        )
        return True
    except Exception as e:
        st.error(f"应用程序初始化失败：{str(e)}")
        logger.error("Initialization error: %s", e)
        return False


def display_header() -> None:
    t = get_translator()
    st.markdown(f'<h1 class="main-header">{t.t("app_title")}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{t.t("app_subtitle")}</p>', unsafe_allow_html=True)

    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        st.markdown(
            f"""
        <div class="warning-box">
        {t.t("warning_no_llm_keys")}
        </div>
        """,
            unsafe_allow_html=True,
        )


def display_sidebar() -> None:
    t = get_translator()

    with st.sidebar:
        st.markdown(f"### {t.t('sidebar_config')}")
        st.caption(t.t("sidebar_config_auto"))

        col_lang, col_reload = st.columns(2)
        with col_lang:
            language = st.selectbox(
                t.t("language"),
                options=["zh", "en"],
                format_func=lambda x: t.t("language_en") if x == "en" else t.t("language_zh"),
                index=0 if st.session_state.current_language == "zh" else 1,
            )
            if language != st.session_state.current_language:
                st.session_state.current_language = language
                st.session_state.translator.set_language(language)
                st.rerun()

        with col_reload:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t.t("config_reload"), use_container_width=True):
                initialize_app(None)
                st.rerun()

        if st.session_state.config:
            config = st.session_state.config

            st.info(f"**{t.t('sidebar_model')}:** {config.llm_model}")
            st.info(f"**{t.t('sidebar_max_papers')}:** {config.max_papers_to_retrieve}")
            st.info(f"**{t.t('sidebar_temperature')}:** {config.temperature}")



            api_status = []
            if config.openai_api_key:
                api_status.append(t.t("api_openai"))
            if config.anthropic_api_key:
                api_status.append(t.t("api_anthropic"))
            if config.semantic_scholar_api_key:
                api_status.append(t.t("api_semantic_scholar_pro"))
            else:
                api_status.append(t.t("api_semantic_scholar_free"))

            st.info(f"**{t.t('sidebar_api_status')}:** {', '.join(api_status)}")

            st.markdown("---")
            st.markdown(f"#### {t.t('network_status')}")

            if st.session_state.orchestrator:
                if st.button(t.t("network_check")):
                    with st.spinner(t.t("network_checking")):
                        connection_status = st.session_state.orchestrator.check_api_connection()

                    ss_status = connection_status.get("semantic_scholar", {})
                    if ss_status.get("connected"):
                        st.success(
                            f"{t.t('network_connected')} ({ss_status.get('response_time', 0):.2f}s)"
                        )
                    else:
                        st.error(
                            t.t(
                                "network_connection_issue",
                                message=ss_status.get("message", "Unknown error"),
                            )
                        )

                    st.session_state.last_connection_status = connection_status

            if "last_connection_status" in st.session_state:
                ss_status = st.session_state.last_connection_status.get("semantic_scholar", {})
                if ss_status.get("connected"):
                    st.success(
                        f"{t.t('network_connected')} ({ss_status.get('response_time', 0):.2f}s)"
                    )
                elif ss_status.get("status"):
                    st.error(
                        t.t(
                            "network_connection_issue",
                            message=ss_status.get("message", "Unknown error"),
                        )
                    )

        st.markdown("---")
        st.markdown(f"### {t.t('sidebar_how_it_works')}")

        steps = t.t("sidebar_how_it_works_steps")
        steps_html = ""
        if isinstance(steps, list):
            for i, step in enumerate(steps, 1):
                steps_html += f"{i}. **{step}**<br>"
        else:
            steps_html = str(steps)

        st.markdown(
            f"""
        {steps_html}

        **{t.t('sidebar_zero_hallucination')}**
        """
        )

        st.markdown("---")
        st.markdown(f"### {t.t('sidebar_resources')}")
        st.markdown(
            """
        - [Semantic Scholar API](https://www.semanticscholar.org/product/api)
        - [OpenAI API](https://platform.openai.com/)
        - [Anthropic API](https://console.anthropic.com/)
        """
        )


def display_search_form() -> Tuple[str, int, bool]:
    t = get_translator()
    st.markdown(f"### {t.t('search_title')}")

    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            t.t("search_input_label"),
            placeholder=t.t("search_input_placeholder"),
            help=t.t("search_input_help"),
        )

    with col2:
        limit = st.number_input(
            t.t("search_max_papers_label"),
            min_value=1,
            max_value=20,
            value=10,
            help=t.t("search_max_papers_help"),
        )

    search_button = st.button(t.t("search_button"), type="primary", use_container_width=True)

    return query, int(limit), search_button


def display_paper_card(paper: Paper, index: int) -> None:
    t = get_translator()

    with st.container():
        st.markdown('<div class="paper-card">', unsafe_allow_html=True)
        st.markdown(f"**[{index}] {paper.title}**")

        authors_str = format_author_names(paper.authors, max_shown=3)

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"*{authors_str}*")
        with col2:
            if paper.year:
                st.markdown(f"**{t.t('paper_year')}:** {paper.year}")
        with col3:
            if paper.citation_count is not None:
                st.markdown(f"**{t.t('paper_citations')}:** {paper.citation_count}")

        if paper.abstract:
            with st.expander(t.t("paper_abstract")):
                st.write(paper.abstract)

        if paper.url:
            st.markdown(f"[📄 {t.t('paper_read_more')}]({paper.url})")

        st.markdown("</div>", unsafe_allow_html=True)


def display_results(result: Any) -> None:
    t = get_translator()

    if result.error:
        st.error(t.t("error_search", error=result.error))
        return

    st.markdown(
        f"""
    <div class="success-box">
    ✅ {t.t('results_found', count=len(result.search_result.papers))} in {result.search_result.search_time:.2f}s.
    Generated answer in {result.processing_time:.2f}s total.
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(f"### {t.t('results_answer')}")
    st.markdown('<div class="answer-container">', unsafe_allow_html=True)

    answer_text = result.llm_response.answer
    answer_text = re.sub(r"\[(\d+)\]", r'<span class="citation">[\1]</span>', answer_text)
    st.markdown(answer_text, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if result.llm_response.citations:
        st.markdown(
            f"### {t.t('results_references')} (cited {len(result.llm_response.citations)} papers)"
        )

        cited_papers = []
        for idx in result.llm_response.citations:
            if idx < len(result.search_result.papers):
                cited_papers.append((idx + 1, result.search_result.papers[idx]))

        cited_papers.sort(key=lambda x: x[0])

        for citation_num, paper in cited_papers:
            display_paper_card(paper, citation_num)

    st.markdown(f"### {t.t('results_references')} ({len(result.search_result.papers)} papers total)")

    cited_indices = set(result.llm_response.citations)
    for idx, paper in enumerate(result.search_result.papers, 1):
        if idx - 1 in cited_indices:
            continue
        display_paper_card(paper, idx)
