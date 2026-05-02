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
    /* ── Header ── */
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        line-height: 1.2;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .sub-header {
        font-size: 1.15rem;
        color: #6B7280;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
    }

    /* ── Stats bar ── */
    .stats-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
    }
    .stat-card {
        flex: 1;
        min-width: 120px;
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.12);
    }
    .stat-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1E3A8A;
        line-height: 1.2;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #6B7280;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.25rem;
    }

    /* ── Paper cards ── */
    .paper-card {
        padding: 1.25rem;
        border-radius: 0.75rem;
        border-left: 4px solid #3B82F6;
        border-top: 1px solid #E5E7EB;
        border-right: 1px solid #E5E7EB;
        border-bottom: 1px solid #E5E7EB;
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-left-color 0.2s ease;
        position: relative;
    }
    .paper-card:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        border-left-color: #2563EB;
    }
    .paper-card-cited {
        border-left: 4px solid #10B981 !important;
        background: linear-gradient(135deg, #F0FDF4 0%, #FFFFFF 100%) !important;
    }
    .paper-card-cited:hover {
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
    }
    .cited-badge {
        display: inline-block;
        background: #D1FAE5;
        color: #065F46;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 9999px;
        margin-left: 0.5rem;
        vertical-align: middle;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .venue-badge {
        display: inline-block;
        background: #F1F5F9;
        color: #475569;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.15rem 0.6rem;
        border-radius: 0.375rem;
        margin-right: 0.5rem;
        font-style: italic;
    }
    .field-badge {
        display: inline-block;
        background: #EFF6FF;
        color: #1D4ED8;
        font-size: 0.7rem;
        font-weight: 500;
        padding: 0.1rem 0.5rem;
        border-radius: 9999px;
        margin-right: 0.3rem;
        margin-bottom: 0.25rem;
    }
    .field-badge-container {
        margin-top: 0.4rem;
        margin-bottom: 0.3rem;
    }

    /* ── Citations ── */
    .citation {
        display: inline-block;
        background-color: #EFF6FF;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
        color: #1D4ED8;
        font-size: 0.9em;
        white-space: nowrap;
    }

    /* ── Callout boxes ── */
    .success-box {
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border-left: 4px solid #10B981;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(16, 185, 129, 0.1);
        font-weight: 500;
    }
    .warning-box {
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
        border-left: 4px solid #F59E0B;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(245, 158, 11, 0.1);
    }

    /* ── Answer container ── */
    .answer-container {
        padding: 1.5rem 2rem;
        border-radius: 0.75rem;
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        margin-bottom: 2rem;
        font-size: 1rem;
        line-height: 1.8;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    /* ── Analysis sections ── */
    .analysis-section {
        padding: 1.5rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #FFFFFF 0%, #F0F9FF 100%);
        border: 1px solid #E0F2FE;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    /* ── Key finding items ── */
    .key-finding-item {
        padding: 0.6rem 0.9rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #FFFBEB 0%, #FFFFFF 100%);
        border-left: 3px solid #F59E0B;
        border-radius: 0 0.5rem 0.5rem 0;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    /* ── Followup cards ── */
    .followup-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
        transition: box-shadow 0.2s ease;
    }

    /* ── Sidebar ── */
    .sidebar-section-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .api-status-row {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.2rem 0;
        font-size: 0.8rem;
    }
    .api-status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        flex-shrink: 0;
    }
    .api-status-dot.connected { background: #10B981; }
    .api-status-dot.error { background: #EF4444; }
    .api-status-dot.unknown { background: #9CA3AF; }

    /* ── Divider ── */
    .section-divider {
        margin: 2rem 0;
        border: none;
        border-top: 1px solid #E5E7EB;
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

            st.markdown(
                f'<div class="sidebar-section-title">{t.t("sidebar_config_info")}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div style="font-size:0.85rem; line-height:1.8; padding:0 0.2rem;">
                <b>{t.t('sidebar_model')}:</b> {config.llm_model}<br>
                <b>{t.t('sidebar_max_papers')}:</b> {config.max_papers_to_retrieve}<br>
                <b>{t.t('sidebar_temperature')}:</b> {config.temperature}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="sidebar-section-title">{t.t("sidebar_api_section")}</div>',
                unsafe_allow_html=True,
            )

            api_status = []
            if config.openai_api_key:
                api_status.append(("connected", t.t("api_openai")))
            else:
                api_status.append(("unknown", "OpenAI"))
            if config.anthropic_api_key:
                api_status.append(("connected", t.t("api_anthropic")))
            else:
                api_status.append(("unknown", "Anthropic"))
            if config.semantic_scholar_api_key:
                api_status.append(("connected", t.t("api_semantic_scholar_pro")))
            else:
                api_status.append(("connected", t.t("api_semantic_scholar_free")))
            api_status.append(("connected", "arXiv API"))
            if config.pubmed_api_key:
                api_status.append(("connected", "PubMed API (key)"))
            else:
                api_status.append(("connected", "PubMed API (free)"))
            if config.openalex_api_key:
                api_status.append(("connected", "OpenAlex API (key)"))
            else:
                api_status.append(("connected", "OpenAlex API (free)"))

            for dot_class, label in api_status:
                st.markdown(
                    f'<div class="api-status-row">'
                    f'<span class="api-status-dot {dot_class}"></span> {label}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown(f"#### {t.t('network_status')}")

            if st.button(t.t("network_check")):
                with st.spinner(t.t("network_checking")):
                    connection_status = st.session_state.orchestrator.check_api_connection()
                st.session_state.last_connection_status = connection_status

            if "last_connection_status" in st.session_state:
                connection_status = st.session_state.last_connection_status

                apis = [
                    ("Semantic Scholar", connection_status.get("semantic_scholar", {})),
                    ("arXiv", connection_status.get("arxiv", {})),
                    ("PubMed", connection_status.get("pubmed", {})),
                    ("OpenAlex", connection_status.get("openalex", {})),
                ]
                for name, status in apis:
                    if status.get("status"):
                        dot = "connected" if status.get("connected") else "error"
                        rt = status.get("response_time", 0)
                        label = f"{name} ({rt:.2f}s)" if rt else name
                        st.markdown(
                            f'<div class="api-status-row">'
                            f'<span class="api-status-dot {dot}"></span> {label}'
                            f'</div>',
                            unsafe_allow_html=True,
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


def display_stats_bar(result: Any) -> None:
    """Render 4 metric cards summarizing the search results."""
    t = get_translator()
    papers = result.search_result.papers
    if not papers:
        return

    total_citations = sum(p.citation_count or 0 for p in papers)
    years = [p.year for p in papers if p.year]
    avg_cit = int(total_citations / len(papers)) if papers else 0

    st.markdown('<div class="stats-bar">', unsafe_allow_html=True)

    st.markdown(f'''
        <div class="stat-card">
            <div class="stat-value">{len(papers)}</div>
            <div class="stat-label">{t.t("stats_total_papers")}</div>
        </div>
    ''', unsafe_allow_html=True)

    st.markdown(f'''
        <div class="stat-card">
            <div class="stat-value">{total_citations:,}</div>
            <div class="stat-label">{t.t("stats_total_citations")}</div>
        </div>
    ''', unsafe_allow_html=True)

    st.markdown(f'''
        <div class="stat-card">
            <div class="stat-value">{avg_cit:,}</div>
            <div class="stat-label">{t.t("stats_avg_citations")}</div>
        </div>
    ''', unsafe_allow_html=True)

    if years:
        yr_min, yr_max = min(years), max(years)
        date_str = f"{yr_min}" if yr_min == yr_max else f"{yr_min} - {yr_max}"
        st.markdown(f'''
            <div class="stat-card">
                <div class="stat-value" style="font-size:1.3rem;">{date_str}</div>
                <div class="stat-label">{t.t("stats_date_range")}</div>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def display_paper_card(paper: Paper, index: int, is_cited: bool = False) -> None:
    t = get_translator()
    card_class = "paper-card paper-card-cited" if is_cited else "paper-card"

    with st.container():
        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

        cited_html = (
            f' <span class="cited-badge">{t.t("paper_cited_in_answer")}</span>'
            if is_cited else ""
        )
        st.markdown(f"**[{index}] {paper.title}**{cited_html}", unsafe_allow_html=True)

        if paper.venue:
            st.markdown(
                f'<span class="venue-badge">📖 {paper.venue}</span>',
                unsafe_allow_html=True,
            )

        authors_str = format_author_names(paper.authors, max_shown=3)
        st.markdown(f"*{authors_str}*")

        col1, col2, col3 = st.columns(3)
        with col1:
            if paper.year:
                st.markdown(f"**{t.t('paper_year')}:** {paper.year}")
        with col2:
            if paper.citation_count is not None:
                st.markdown(f"**{t.t('paper_citations')}:** {paper.citation_count}")
        with col3:
            if paper.reference_count is not None:
                st.markdown(f"**{t.t('paper_reference_count')}:** {paper.reference_count}")

        if paper.fields_of_study:
            badges = "".join(
                f'<span class="field-badge">{f}</span>' for f in paper.fields_of_study
            )
            st.markdown(
                f'<div class="field-badge-container">{badges}</div>',
                unsafe_allow_html=True,
            )

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

    display_stats_bar(result)

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
        is_cited = (idx - 1) in cited_indices
        display_paper_card(paper, idx, is_cited=is_cited)
