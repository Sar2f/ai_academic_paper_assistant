#!/usr/bin/env python3
"""
AI Academic Paper Assistant - Streamlit Application
A web application that searches for academic papers and generates answers using LLMs.
"""

import os
import re
import logging
import streamlit as st
from dotenv import load_dotenv

from src.utils.config_manager import ConfigManager
from src.core.orchestrator import AcademicPaperOrchestrator
from src.i18n.translations import Translator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="AI 学术论文助手", page_icon="📚", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better styling
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None
if "last_query" not in st.session_state:
    st.session_state.last_query = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "config" not in st.session_state:
    st.session_state.config = None
if "config_manager" not in st.session_state:
    st.session_state.config_manager = ConfigManager()
if "current_language" not in st.session_state:
    st.session_state.current_language = "zh"  # Default to Chinese
if "translator" not in st.session_state:
    st.session_state.translator = Translator("zh")


def get_translator() -> Translator:
    """Get the current translator instance."""
    if "translator" not in st.session_state:
        st.session_state.translator = Translator(st.session_state.get("current_language", "zh"))
    return st.session_state.translator


def initialize_app(config_source: str = None):
    """Initialize the application with configuration."""
    try:
        # Load configuration
        config_manager = st.session_state.config_manager
        config = config_manager.load_config(config_source)

        # Initialize orchestrator
        orchestrator = AcademicPaperOrchestrator(config)

        # Store in session state
        st.session_state.config = config
        st.session_state.orchestrator = orchestrator

        logger.info(f"Application initialized successfully from {config_manager.current_source}")
        return True

    except Exception as e:
        st.error(f"应用程序初始化失败：{str(e)}")
        logger.error(f"Initialization error: {e}")
        return False


def display_header():
    """Display the application header."""
    t = get_translator()

    st.markdown(f'<h1 class="main-header">{t.t("app_title")}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{t.t("app_subtitle")}</p>', unsafe_allow_html=True)

    # Display warning about API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        st.markdown(
            f"""
        <div class="warning-box">
        {t.t("warning_no_llm_keys")}
        </div>
        """,
            unsafe_allow_html=True,
        )


def display_sidebar():
    """Display the sidebar with configuration and information."""
    t = get_translator()

    with st.sidebar:
        st.markdown(f"### {t.t('sidebar_config')}")

        # Language selection
        col1, col2 = st.columns(2)
        with col1:
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

        with col2:
            # Config source selection
            config_source = st.selectbox(
                t.t("config_source"),
                options=["env", "json", "default"],
                format_func=lambda x: {
                    "env": t.t("config_source_env"),
                    "json": t.t("config_source_json"),
                    "default": t.t("config_source_default"),
                }[x],
                index=0,  # Default to env
            )

        # Reload config button
        if st.button(t.t("config_reload")):
            initialize_app(config_source)
            st.rerun()

        if st.session_state.config:
            config = st.session_state.config

            st.info(f"**{t.t('sidebar_model')}:** {config.llm_model}")
            st.info(f"**{t.t('sidebar_max_papers')}:** {config.max_papers_to_retrieve}")
            st.info(f"**{t.t('sidebar_temperature')}:** {config.temperature}")

            # Mock data warning
            if config.use_mock_data:
                st.warning(t.t("mock_data_warning"))

            # Display API key status
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

            # Network connection check
            st.markdown("---")
            st.markdown(f"#### {t.t('network_status')}")

            if st.session_state.orchestrator:
                if st.button(t.t("network_check")):
                    with st.spinner(t.t("network_checking")):
                        connection_status = st.session_state.orchestrator.check_api_connection()

                    # Display Semantic Scholar connection status
                    ss_status = connection_status.get("semantic_scholar", {})
                    if ss_status.get("connected"):
                        st.success(f"{t.t('network_connected')} ({ss_status.get('response_time', 0):.2f}s)")
                    elif connection_status.get("use_mock_data"):
                        st.warning(t.t("network_disconnected"))
                    else:
                        st.error(t.t("network_connection_issue", message=ss_status.get("message", "Unknown error")))

                    # Store connection status in session state
                    st.session_state.last_connection_status = connection_status

            # Show last connection status if available
            if "last_connection_status" in st.session_state:
                ss_status = st.session_state.last_connection_status.get("semantic_scholar", {})
                if ss_status.get("connected"):
                    st.success(f"{t.t('network_connected')} ({ss_status.get('response_time', 0):.2f}s)")
                elif st.session_state.last_connection_status.get("use_mock_data"):
                    st.warning(t.t("network_disconnected"))
                elif ss_status.get("status"):
                    st.error(t.t("network_connection_issue", message=ss_status.get("message", "Unknown error")))

        st.markdown("---")
        st.markdown(f"### {t.t('sidebar_how_it_works')}")

        steps = t.t("sidebar_how_it_works_steps")
        steps_html = ""
        # Check if steps is a list or string
        if isinstance(steps, list):
            for i, step in enumerate(steps, 1):
                steps_html += f"{i}. **{step}**<br>"
        else:
            # If it's a string, just use it as-is
            steps_html = steps

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
        - [Project GitHub](https://github.com/)
        """
        )


def display_search_form():
    """Display the search form."""
    t = get_translator()

    st.markdown(f"### {t.t('search_title')}")

    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            t.t("search_input_label"), placeholder=t.t("search_input_placeholder"), help=t.t("search_input_help")
        )

    with col2:
        limit = st.number_input(
            t.t("search_max_papers_label"), min_value=1, max_value=20, value=10, help=t.t("search_max_papers_help")
        )

    search_button = st.button(t.t("search_button"), type="primary", use_container_width=True)

    return query, limit, search_button


def display_paper_card(paper, index):
    """Display a paper card in the references section."""
    t = get_translator()

    with st.container():
        st.markdown('<div class="paper-card">', unsafe_allow_html=True)

        # Title with citation number
        st.markdown(f"**[{index}] {paper.title}**")

        # Authors and year
        author_names = [author.name for author in paper.authors[:3]]
        if len(paper.authors) > 3:
            author_names.append("et al.")
        authors_str = ", ".join(author_names)

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"*{authors_str}*")
        with col2:
            if paper.year:
                st.markdown(f"**{t.t('paper_year')}:** {paper.year}")
        with col3:
            if paper.citation_count is not None:
                st.markdown(f"**{t.t('paper_citations')}:** {paper.citation_count}")

        # Abstract preview
        if paper.abstract:
            with st.expander(t.t("paper_abstract")):
                st.write(paper.abstract)

        # Links
        if paper.url:
            st.markdown(f"[📄 {t.t('paper_read_more')}]({paper.url})")

        st.markdown("</div>", unsafe_allow_html=True)


def display_results(result):
    """Display the processing results."""
    t = get_translator()

    if result.error:
        st.error(t.t("error_search", error=result.error))
        return

    # Display success message
    st.markdown(
        f"""
    <div class="success-box">
    ✅ {t.t('results_found', count=len(result.search_result.papers))} in {result.search_result.search_time:.2f}s.
    Generated answer in {result.processing_time:.2f}s total.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Display the answer
    st.markdown(f"### {t.t('results_answer')}")
    st.markdown('<div class="answer-container">', unsafe_allow_html=True)

    # Process answer to highlight citations
    answer_text = result.llm_response.answer
    # Simple citation highlighting
    answer_text = re.sub(r"\[(\d+)\]", r'<span class="citation">[\1]</span>', answer_text)
    st.markdown(answer_text, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Display referenced papers
    if result.llm_response.citations:
        st.markdown(f"### {t.t('results_references')} (cited {len(result.llm_response.citations)} papers)")

        cited_papers = []
        for idx in result.llm_response.citations:
            if idx < len(result.search_result.papers):
                cited_papers.append((idx + 1, result.search_result.papers[idx]))

        # Sort by citation number
        cited_papers.sort(key=lambda x: x[0])

        for citation_num, paper in cited_papers:
            display_paper_card(paper, citation_num)

    # Display all papers found
    st.markdown(f"### {t.t('results_references')} ({len(result.search_result.papers)} papers total)")

    cited_indices = set(result.llm_response.citations)
    for idx, paper in enumerate(result.search_result.papers, 1):
        # Skip papers that were already shown as citations
        if idx - 1 in cited_indices:
            continue
        display_paper_card(paper, idx)


def main():
    """Main application function."""
    t = get_translator()

    # Display header
    display_header()

    # Initialize application if not already done
    if st.session_state.orchestrator is None:
        if not initialize_app():
            st.stop()

    # Display sidebar
    display_sidebar()

    # Display search form
    query, limit, search_button = display_search_form()

    # Handle search
    if search_button and query:
        with st.spinner(t.t("searching")):
            result = st.session_state.orchestrator.process_query(query, limit)
            st.session_state.last_query = query
            st.session_state.last_result = result

        # Display results
        display_results(result)

    # Display previous results if available
    elif st.session_state.last_result and st.session_state.last_query:
        st.markdown(f"### 📋 {t.t('last_search', query=st.session_state.last_query)}")
        display_results(st.session_state.last_result)

    # Footer
    st.markdown("---")
    st.markdown(f"<div style='text-align: center; color: #6B7280;'>{t.t('footer')}</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
