"""
Streamlit layout and widgets. No retrieval or LLM calls here.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional, Tuple

import streamlit as st

from ..core.orchestrator import AcademicPaperOrchestrator
from ..i18n.translations import Translator
from ..models.paper import Paper, format_author_names
from ..utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)

APP_CSS = """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6B7280;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    .paper-card {
        padding: 1.25rem;
        border-radius: 0.75rem;
        border-left: 4px solid #3B82F6;
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border-top: 1px solid #E5E7EB;
    }
    .paper-card:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    }
    .citation {
        background-color: #EFF6FF;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
        color: #1D4ED8;
        font-size: 0.9em;
    }
    .success-box {
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border-left: 4px solid #10B981;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(16, 185, 129, 0.1);
    }
    .warning-box {
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
        border-left: 4px solid #F59E0B;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(245, 158, 11, 0.1);
    }
    .answer-container {
        padding: 1.5rem 2rem;
        border-radius: 0.75rem;
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        margin-bottom: 2rem;
        line-height: 1.7;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    .analysis-section {
        padding: 1.5rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #FFFFFF 0%, #F0F9FF 100%);
        border: 1px solid #E0F2FE;
        margin-bottom: 1.5rem;
    }
    .followup-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        margin-bottom: 0.75rem;
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
            api_status.append("arXiv API")
            if config.pubmed_api_key:
                api_status.append("PubMed API (key)")
            else:
                api_status.append("PubMed API (free)")
            if config.openalex_api_key:
                api_status.append("OpenAlex API (key)")
            else:
                api_status.append("OpenAlex API (free)")

            st.info(f"**{t.t('sidebar_api_status')}:** {', '.join(api_status)}")

            st.markdown("---")
            st.markdown(f"#### {t.t('network_status')}")

            if st.button(t.t("network_check")):
                with st.spinner(t.t("network_checking")):
                    connection_status = st.session_state.orchestrator.check_api_connection()
                st.session_state.last_connection_status = connection_status

            if "last_connection_status" in st.session_state:
                connection_status = st.session_state.last_connection_status
                for api_key in ["semantic_scholar", "arxiv", "pubmed", "openalex"]:
                    status = connection_status.get(api_key, {})
                    display_name = api_key.replace("_", " ").title()
                    if status.get("connected"):
                        st.success(f"✅ {display_name} ({status.get('response_time', 0):.2f}s)")
                    elif status.get("status"):
                        st.error(f"❌ {display_name}")

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


def display_cross_paper_analysis(result: Any) -> None:
    t = get_translator()
    analysis = result.cross_paper_analysis

    if not analysis or not analysis.research_trends:
        return

    st.markdown("---")
    st.markdown(f"### 🔬 {t.t('cross_paper_analysis_title')}")
    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)

    st.markdown(analysis.research_trends)

    st.markdown("</div>", unsafe_allow_html=True)

    if analysis.paper_analyses and result.search_result.papers:
        st.markdown("---")
        st.markdown(f"### 📝 {t.t('cross_paper_individual_title')}")
        st.caption(t.t("cross_paper_individual_hint"))

        for i, (paper_analysis, paper) in enumerate(zip(
            analysis.paper_analyses[:5],
            result.search_result.papers[:5]
        )):
            with st.expander(f"📄 [{i+1}] {paper.title[:60]}..."):
                col1, col2 = st.columns(2)
                _truncate = lambda s, n=150: s[:n] + "..." if len(s) > n else s
                with col1:
                    if paper_analysis.keywords:
                        st.markdown(f"**🔑 {t.t('paper_analysis_keywords')}:**")
                        st.markdown(", ".join(paper_analysis.keywords))
                    if paper_analysis.research_method:
                        st.markdown(f"\n**🔬 {t.t('paper_analysis_method')}:** {paper_analysis.research_method}")
                with col2:
                    if paper_analysis.contributions:
                        st.markdown(f"**✨ {t.t('paper_analysis_contributions')}:**")
                        st.markdown(_truncate(paper_analysis.contributions))
                    if paper_analysis.limitations:
                        st.markdown(f"\n**⚠️ {t.t('paper_analysis_limitations')}:**")
                        st.markdown(_truncate(paper_analysis.limitations))


def display_followup_section(result: Any) -> None:
    t = get_translator()

    if "followup_history" not in st.session_state:
        st.session_state.followup_history = []

    st.markdown("---")
    st.markdown(f"### 💬 {t.t('followup_title')}")

    followup_query = st.text_input(
        t.t("followup_input_label"),
        placeholder=t.t("followup_input_placeholder"),
        key="followup_input"
    )

    if st.button(t.t("followup_button"), type="secondary", use_container_width=True):
        if followup_query.strip():
            with st.spinner(t.t("followup_processing")):
                if st.session_state.orchestrator:
                    followup_response = st.session_state.orchestrator.process_followup(
                        followup_query=followup_query,
                        papers=result.search_result.papers,
                        previous_answer=result.llm_response.answer
                    )

                    st.session_state.followup_history.append({
                        "query": followup_query,
                        "answer": followup_response.answer,
                        "error": followup_response.error
                    })

    if st.session_state.followup_history:
        for i, followup in enumerate(st.session_state.followup_history, 1):
            with st.expander(f"🔍 {t.t('followup_question')} {i}: {followup['query'][:50]}..."):
                if followup.get("error"):
                    st.error(followup["answer"])
                else:
                    answer_text = re.sub(r"\[(\d+)\]", r'<span class="citation">[\1]</span>', followup["answer"])
                    st.markdown(answer_text, unsafe_allow_html=True)


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

    display_cross_paper_analysis(result)

    st.markdown(f"### {t.t('results_answer')}")
    st.markdown('<div class="answer-container">', unsafe_allow_html=True)

    answer_text = result.llm_response.answer
    answer_text = re.sub(r"\[(\d+)\]", r'<span class="citation">[\1]</span>', answer_text)
    st.markdown(answer_text, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    display_followup_section(result)

    st.markdown(f"### {t.t('results_references')} ({len(result.search_result.papers)} papers)")

    cited_indices = set(result.llm_response.citations)

    for idx, paper in enumerate(result.search_result.papers, 1):
        display_paper_card(paper, idx)
