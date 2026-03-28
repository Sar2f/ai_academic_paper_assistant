#!/usr/bin/env python3
"""
AI Academic Paper Assistant — Streamlit entrypoint.
界面与编排见 src/ui；业务编排见 src/core/orchestrator。
"""

import logging

import streamlit as st
from dotenv import load_dotenv

from src.ui.streamlit_components import (
    APP_CSS,
    display_header,
    display_results,
    display_search_form,
    display_sidebar,
    get_translator,
    initialize_app,
)
from src.utils.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

st.set_page_config(
    page_title="AI 学术论文助手",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)

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
    st.session_state.current_language = "zh"
if "translator" not in st.session_state:
    from src.i18n.translations import Translator

    st.session_state.translator = Translator("zh")


def main() -> None:
    t = get_translator()

    display_header()

    if st.session_state.orchestrator is None:
        if not initialize_app():
            st.stop()

    display_sidebar()

    query, limit, search_button = display_search_form()

    if search_button:
        raw = (query or "").strip()
        if not raw:
            st.warning(t.t("search_empty_query"))
        else:
            with st.spinner(t.t("searching")):
                result = st.session_state.orchestrator.process_query(raw, limit)
                st.session_state.last_query = raw
                st.session_state.last_result = result
            display_results(result)

    elif st.session_state.last_result and st.session_state.last_query:
        st.markdown(f"### 📋 {t.t('last_search', query=st.session_state.last_query)}")
        display_results(st.session_state.last_result)

    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #6B7280;'>{t.t('footer')}</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
