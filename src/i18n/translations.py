"""
Internationalization translations for AI Academic Paper Assistant.
Supports English (en) and Chinese (zh).
"""

translations = {
    "en": {
        # App titles and headers
        "app_title": "📚 AI Academic Paper Assistant",
        "app_subtitle": "Search academic papers and get zero-hallucination AI-powered summaries",
        "last_search": "Previous Search: '{query}'",
        
        # Sidebar
        "sidebar_config": "⚙️ Configuration",
        "sidebar_model": "Model",
        "sidebar_max_papers": "Max Papers",
        "sidebar_temperature": "Temperature",
        "sidebar_api_status": "API Status",
        "sidebar_how_it_works": "📖 How It Works",
        "sidebar_how_it_works_steps": [
            "Enter your research question in the search box",
            "Search for relevant academic papers",
            "Get AI-powered answer based on real papers",
            "View citations with links to original papers"
        ],
        "sidebar_zero_hallucination": "Zero Hallucination Guarantee: All answers strictly based on retrieved papers.",
        "sidebar_resources": "🔗 Resources",
        
        # Search form
        "search_title": "🔍 Search Academic Papers",
        "search_input_label": "Enter your research question:",
        "search_input_placeholder": "e.g., 'What are the latest advances in quantum computing?'",
        "search_input_help": "Be more specific for better results",
        "search_max_papers_label": "Max Papers:",
        "search_max_papers_help": "Number of papers to retrieve",
        "search_button": "🔎 Search & Analyze",
        
        # Results
        "results_found": "Found {count} relevant papers",
        "results_answer": "🤖 AI-Powered Answer",
        "results_references": "📚 References",
        
        # Paper card
        "paper_year": "Year",
        "paper_citations": "Citations",
        "paper_abstract": "Abstract",
        "paper_read_more": "Read Paper",
        
        # Warnings and errors
        "warning_no_llm_keys": "⚠️ No LLM API keys detected. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file to enable AI-powered answers. Semantic Scholar search will still work.",
        "error_initialization": "Application initialization failed: {error}",
        "error_search": "Error: {error}",
        "searching": "🔍 Searching for academic papers...",
        
        # API status messages
        "api_openai": "✅ OpenAI",
        "api_anthropic": "✅ Anthropic",
        "api_semantic_scholar": "✅ Semantic Scholar",
        "api_semantic_scholar_pro": "✅ Semantic Scholar (Pro)",
        "api_semantic_scholar_free": "✅ Semantic Scholar (Free)",
        
        # Footer
        "footer": "AI Academic Paper Assistant • Zero Hallucination Guarantee • Built with ❤️ using Streamlit, Semantic Scholar, and LLMs",
        
        # Configuration
        "config_use_mock_data": "Use Mock Data",
        "config_use_mock_data_help": "Use mock data instead of real API calls (for testing)",
        
        # Language selection
        "language": "Language",
        "language_en": "English",
        "language_zh": "中文",
        
        # Config management
        "config_source": "Config Source",
        "config_source_env": ".env File",
        "config_source_json": "JSON Config",
        "config_source_default": "Default",
        "config_manage": "Manage Configuration",
        "config_create_template": "Create Template",
        "config_save_current": "Save Current",
        "config_reload": "Reload",
        "config_current_source": "Current Source: {source}",
        
        # Network status
        "network_status": "🌐 Network Status",
        "network_connected": "✅ Connected to Semantic Scholar API",
        "network_disconnected": "❌ Not connected - using mock data",
        "network_check": "Check Connection",
        "network_checking": "Checking connection...",
        "network_connection_issue": "Connection issue: {message}",
        
        # Mock data warning
        "mock_data_warning": "⚠️ Using mock data. Set USE_MOCK_DATA=false for real API search.",
    },
    
    "zh": {
        # App titles and headers
        "app_title": "📚 AI 学术论文助手",
        "app_subtitle": "搜索学术论文并获得零幻觉的AI驱动摘要",
        "last_search": "上次搜索：'{query}'",
        
        # Sidebar
        "sidebar_config": "⚙️ 配置",
        "sidebar_model": "模型",
        "sidebar_max_papers": "最大论文数",
        "sidebar_temperature": "温度",
        "sidebar_api_status": "API 状态",
        "sidebar_how_it_works": "📖 工作原理",
        "sidebar_how_it_works_steps": [
            "在搜索框中输入你的研究问题",
            "搜索相关学术论文",
            "获取基于真实论文的AI驱动答案",
            "查看引用，包含原始论文链接"
        ],
        "sidebar_zero_hallucination": "零幻觉保证：所有答案严格基于检索到的论文。",
        "sidebar_resources": "🔗 资源",
        
        # Search form
        "search_title": "🔍 搜索学术论文",
        "search_input_label": "输入你的研究问题：",
        "search_input_placeholder": "例如：'量子计算的最新进展是什么？'",
        "search_input_help": "更具体以获得更好结果",
        "search_max_papers_label": "最大论文数：",
        "search_max_papers_help": "要检索的论文数量",
        "search_button": "🔎 搜索与分析",
        
        # Results
        "results_found": "找到 {count} 篇相关论文",
        "results_answer": "🤖 AI 驱动答案",
        "results_references": "📚 参考文献",
        
        # Paper card
        "paper_year": "年份",
        "paper_citations": "引用",
        "paper_abstract": "摘要",
        "paper_read_more": "阅读论文",
        
        # Warnings and errors
        "warning_no_llm_keys": "⚠️ 未检测到 LLM API 密钥。请在 .env 文件中设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 以启用 AI 驱动的答案。Semantic Scholar 搜索仍可工作。",
        "error_initialization": "应用程序初始化失败：{error}",
        "error_search": "错误：{error}",
        "searching": "🔍 正在搜索学术论文...",
        
        # API status messages
        "api_openai": "✅ OpenAI",
        "api_anthropic": "✅ Anthropic",
        "api_semantic_scholar": "✅ Semantic Scholar",
        "api_semantic_scholar_pro": "✅ Semantic Scholar (Pro)",
        "api_semantic_scholar_free": "✅ Semantic Scholar (Free)",
        
        # Footer
        "footer": "AI 学术论文助手 • 零幻觉保证 • 使用 Streamlit、Semantic Scholar 和 LLMs 构建，用心打造 ❤️",
        
        # Configuration
        "config_use_mock_data": "使用模拟数据",
        "config_use_mock_data_help": "使用模拟数据而不是真实API调用（用于测试）",
        
        # Language selection
        "language": "语言",
        "language_en": "English",
        "language_zh": "中文",
        
        # Config management
        "config_source": "配置源",
        "config_source_env": ".env 文件",
        "config_source_json": "JSON 配置",
        "config_source_default": "默认",
        "config_manage": "管理配置",
        "config_create_template": "创建模板",
        "config_save_current": "保存当前",
        "config_reload": "重新加载",
        "config_current_source": "当前配置源：{source}",
        
        # Network status
        "network_status": "🌐 网络状态",
        "network_connected": "✅ 已连接到 Semantic Scholar API",
        "network_disconnected": "❌ 未连接 - 使用模拟数据",
        "network_check": "检查连接",
        "network_checking": "检查连接状态...",
        "network_connection_issue": "连接问题: {message}",
        
        # Mock data warning
        "mock_data_warning": "⚠️ 使用模拟数据。设置 USE_MOCK_DATA=false 进行真实 API 搜索。",
    }
}


class Translator:
    """Simple translation helper."""
    
    def __init__(self, language="zh"):
        self.language = language
    
    def t(self, key: str, **kwargs) -> str:
        """
        Get translation for a key.
        
        Args:
            key: Translation key
            **kwargs: Formatting arguments
            
        Returns:
            Translated string
        """
        # Get translation for current language, fallback to English if not found
        lang_dict = translations.get(self.language, translations["en"])
        text = lang_dict.get(key, translations["en"].get(key, key))
        
        # Format with kwargs if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass  # Return text as-is if formatting fails
        
        return text
    
    def set_language(self, language: str):
        """Set the current language."""
        if language in translations:
            self.language = language
        else:
            self.language = "en"  # Default to English