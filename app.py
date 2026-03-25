#!/usr/bin/env python3
"""
AI Academic Paper Assistant - Streamlit Application
A web application that searches for academic papers and generates answers using LLMs.
"""

import os
import sys
import logging
import streamlit as st
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import AppConfig
from src.core.orchestrator import AcademicPaperOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Academic Paper Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
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
""", unsafe_allow_html=True)

# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'last_query' not in st.session_state:
    st.session_state.last_query = None
if 'last_result' not in st.session_state:
    st.session_state.last_result = None
if 'config' not in st.session_state:
    st.session_state.config = None


def initialize_app():
    """Initialize the application with configuration."""
    try:
        # Load configuration
        config = AppConfig.from_env()
        config.validate()
        
        # Initialize orchestrator
        orchestrator = AcademicPaperOrchestrator(config)
        
        # Store in session state
        st.session_state.config = config
        st.session_state.orchestrator = orchestrator
        
        logger.info("Application initialized successfully")
        return True
        
    except Exception as e:
        st.error(f"Failed to initialize application: {str(e)}")
        logger.error(f"Initialization error: {e}")
        return False


def display_header():
    """Display the application header."""
    st.markdown('<h1 class="main-header">📚 AI Academic Paper Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Search for academic papers and get AI-powered summaries with zero hallucination</p>', unsafe_allow_html=True)
    
    # Display warning about API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        st.markdown("""
        <div class="warning-box">
        ⚠️ <strong>No LLM API key detected.</strong> Please set either OPENAI_API_KEY or ANTHROPIC_API_KEY 
        in your .env file to enable AI-powered answers. Semantic Scholar search will still work.
        </div>
        """, unsafe_allow_html=True)


def display_sidebar():
    """Display the sidebar with configuration and information."""
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        if st.session_state.config:
            config = st.session_state.config
            
            st.info(f"**Model:** {config.llm_model}")
            st.info(f"**Max Papers:** {config.max_papers_to_retrieve}")
            st.info(f"**Temperature:** {config.temperature}")
            
            # Display API key status
            api_status = []
            if config.openai_api_key:
                api_status.append("✅ OpenAI")
            if config.anthropic_api_key:
                api_status.append("✅ Anthropic")
            if config.semantic_scholar_api_key:
                api_status.append("✅ Semantic Scholar (Pro)")
            else:
                api_status.append("✅ Semantic Scholar (Free)")
            
            st.info(f"**API Status:** {', '.join(api_status)}")
        
        st.markdown("---")
        st.markdown("### 📖 How It Works")
        st.markdown("""
        1. **Enter your research question** in the search box
        2. **Search** for relevant academic papers
        3. **Get AI-powered answer** based on real papers
        4. **Review references** with links to original papers
        
        **Zero Hallucination Guarantee:** All answers are strictly based on retrieved papers.
        """)
        
        st.markdown("---")
        st.markdown("### 🔗 Resources")
        st.markdown("""
        - [Semantic Scholar API](https://www.semanticscholar.org/product/api)
        - [OpenAI API](https://platform.openai.com/)
        - [Anthropic API](https://console.anthropic.com/)
        - [Project GitHub](https://github.com/)
        """)


def display_search_form():
    """Display the search form."""
    st.markdown("### 🔍 Search for Academic Papers")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Enter your research question:",
            placeholder="e.g., 'What are the latest advancements in quantum computing?'",
            help="Be specific for better results"
        )
    
    with col2:
        limit = st.number_input(
            "Max papers:",
            min_value=1,
            max_value=20,
            value=10,
            help="Number of papers to retrieve"
        )
    
    search_button = st.button("🔎 Search & Analyze", type="primary", use_container_width=True)
    
    return query, limit, search_button


def display_paper_card(paper, index):
    """Display a paper card in the references section."""
    with st.container():
        st.markdown(f'<div class="paper-card">', unsafe_allow_html=True)
        
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
                st.markdown(f"**Year:** {paper.year}")
        with col3:
            if paper.citation_count is not None:
                st.markdown(f"**Citations:** {paper.citation_count}")
        
        # Abstract preview
        if paper.abstract:
            abstract_preview = paper.abstract[:200] + "..." if len(paper.abstract) > 200 else paper.abstract
            with st.expander("Abstract"):
                st.write(paper.abstract)
        
        # Links
        if paper.url:
            st.markdown(f"[📄 View Paper]({paper.url})")
        
        st.markdown('</div>', unsafe_allow_html=True)


def display_results(result):
    """Display the processing results."""
    if result.error:
        st.error(f"Error: {result.error}")
        return
    
    # Display success message
    st.markdown(f"""
    <div class="success-box">
    ✅ Found {len(result.search_result.papers)} relevant papers in {result.search_result.search_time:.2f}s. 
    Generated answer in {result.processing_time:.2f}s total.
    </div>
    """, unsafe_allow_html=True)
    
    # Display the answer
    st.markdown("### 📝 AI-Powered Answer")
    st.markdown('<div class="answer-container">', unsafe_allow_html=True)
    
    # Process answer to highlight citations
    answer_text = result.llm_response.answer
    # Simple citation highlighting (can be enhanced)
    import re
    answer_text = re.sub(r'\[(\d+)\]', r'<span class="citation">[\1]</span>', answer_text)
    st.markdown(answer_text, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display referenced papers
    if result.llm_response.citations:
        st.markdown(f"### 📚 Referenced Papers ({len(result.llm_response.citations)} papers cited)")
        
        cited_papers = []
        for idx in result.llm_response.citations:
            if idx < len(result.search_result.papers):
                cited_papers.append((idx + 1, result.search_result.papers[idx]))
        
        # Sort by citation number
        cited_papers.sort(key=lambda x: x[0])
        
        for citation_num, paper in cited_papers:
            display_paper_card(paper, citation_num)
    
    # Display all papers found
    st.markdown(f"### 📄 All Papers Found ({len(result.search_result.papers)} total)")
    
    for idx, paper in enumerate(result.search_result.papers, 1):
        # Skip papers that were already shown as citations
        if idx - 1 in result.llm_response.citations:
            continue
        display_paper_card(paper, idx)


def main():
    """Main application function."""
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
        with st.spinner("🔍 Searching for academic papers..."):
            result = st.session_state.orchestrator.process_query(query, limit)
            st.session_state.last_query = query
            st.session_state.last_result = result
        
        # Display results
        display_results(result)
    
    # Display previous results if available
    elif st.session_state.last_result and st.session_state.last_query:
        st.markdown(f"### 📋 Previous Search: '{st.session_state.last_query}'")
        display_results(st.session_state.last_result)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #6B7280;'>"
        "AI Academic Paper Assistant • Zero Hallucination Guarantee • "
        "Built with ❤️ using Streamlit, Semantic Scholar, and LLMs"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()