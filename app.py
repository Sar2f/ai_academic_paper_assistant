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
    page_title="AI 学术论文助手",
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
        st.error(f"应用程序初始化失败：{str(e)}")
        logger.error(f"Initialization error: {e}")
        return False


def display_header():
    """Display the application header."""
    st.markdown('<h1 class="main-header">📚 AI 学术论文助手</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">搜索学术论文并获得零幻觉的AI驱动摘要</p>', unsafe_allow_html=True)
    
    # Display warning about API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        st.markdown("""
        <div class="warning-box">
        ⚠️ <strong>未检测到 LLM API 密钥。</strong> 请在 .env 文件中设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 
        以启用 AI 驱动的答案。Semantic Scholar 搜索仍可工作。
        </div>
        """, unsafe_allow_html=True)


def display_sidebar():
    """Display the sidebar with configuration and information."""
    with st.sidebar:
        st.markdown("### ⚙️ 配置")
        
        if st.session_state.config:
            config = st.session_state.config
            
            st.info(f"**模型:** {config.llm_model}")
            st.info(f"**最大论文数:** {config.max_papers_to_retrieve}")
            st.info(f"**温度:** {config.temperature}")
            
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
            
            st.info(f"**API 状态:** {', '.join(api_status)}")
        
        st.markdown("---")
        st.markdown("### 📖 工作原理")
        st.markdown("""
        1. **在搜索框中输入你的研究问题**
        2. **搜索**相关学术论文
        3. **获取基于真实论文的AI驱动答案**
        4. **查看引用**，包含原始论文链接
        
        **零幻觉保证：** 所有答案严格基于检索到的论文。
        """)
        
        st.markdown("---")
        st.markdown("### 🔗 资源")
        st.markdown("""
        - [Semantic Scholar API](https://www.semanticscholar.org/product/api)
        - [OpenAI API](https://platform.openai.com/)
        - [Anthropic API](https://console.anthropic.com/)
        - [Project GitHub](https://github.com/)
        """)


def display_search_form():
    """Display the search form."""
    st.markdown("### 🔍 搜索学术论文")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "输入你的研究问题：",
            placeholder="例如：'量子计算的最新进展是什么？'",
            help="更具体以获得更好结果"
        )
    
    with col2:
        limit = st.number_input(
            "最大论文数：",
            min_value=1,
            max_value=20,
            value=10,
            help="要检索的论文数量"
        )
    
    search_button = st.button("🔎 搜索与分析", type="primary", use_container_width=True)
    
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
                st.markdown(f"**年份:** {paper.year}")
        with col3:
            if paper.citation_count is not None:
                st.markdown(f"**引用次数:** {paper.citation_count}")
        
        # Abstract preview
        if paper.abstract:
            abstract_preview = paper.abstract[:200] + "..." if len(paper.abstract) > 200 else paper.abstract
            with st.expander("摘要"):
                st.write(paper.abstract)
        
        # Links
        if paper.url:
            st.markdown(f"[📄 查看论文]({paper.url})")
        
        st.markdown('</div>', unsafe_allow_html=True)


def display_results(result):
    """Display the processing results."""
    if result.error:
        st.error(f"错误：{result.error}")
        return
    
    # Display success message
    st.markdown(f"""
    <div class="success-box">
    ✅ 在 {result.search_result.search_time:.2f}s 内找到 {len(result.search_result.papers)} 篇相关论文。 
    总共在 {result.processing_time:.2f}s 内生成答案。
    </div>
    """, unsafe_allow_html=True)
    
    # Display the answer
    st.markdown("### 📝 AI 驱动答案")
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
        st.markdown(f"### 📚 引用论文（引用了{len(result.llm_response.citations)}篇论文）")
        
        cited_papers = []
        for idx in result.llm_response.citations:
            if idx < len(result.search_result.papers):
                cited_papers.append((idx + 1, result.search_result.papers[idx]))
        
        # Sort by citation number
        cited_papers.sort(key=lambda x: x[0])
        
        for citation_num, paper in cited_papers:
            display_paper_card(paper, citation_num)
    
    # Display all papers found
    st.markdown(f"### 📄 所有找到的论文（共{len(result.search_result.papers)}篇）")
    
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
        with st.spinner("🔍 正在搜索学术论文..."):
            result = st.session_state.orchestrator.process_query(query, limit)
            st.session_state.last_query = query
            st.session_state.last_result = result
        
        # Display results
        display_results(result)
    
    # Display previous results if available
    elif st.session_state.last_result and st.session_state.last_query:
        st.markdown(f"### 📋 上次搜索：'{st.session_state.last_query}'")
        display_results(st.session_state.last_result)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #6B7280;'>"
        "AI 学术论文助手 • 零幻觉保证 • "
        "使用 Streamlit、Semantic Scholar 和 LLMs 构建，用心打造 ❤️"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()