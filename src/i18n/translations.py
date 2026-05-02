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
        "sidebar_config_auto": "Config loads from .env, then config/config.json if present; use Reload to refresh.",
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
        "search_empty_query": "Please enter a search query before clicking Search.",

        # Results
        "results_found": "Found {count} relevant papers",
        "results_answer": "🤖 AI-Powered Answer",
        "results_references": "📚 References",

        # Paper card
        "paper_year": "Year",
        "paper_citations": "Citations",
        "paper_reference_count": "Refs",
        "paper_abstract": "Abstract",
        "paper_read_more": "Read Paper",
        "paper_venue": "Venue",
        "paper_fields_of_study": "Fields",
        "paper_cited_in_answer": "Cited in answer",

        # Warnings and errors
        "warning_no_llm_keys": "⚠️ No LLM API keys detected. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file to enable AI-powered answers. Semantic Scholar search will still work.",
        "error_search": "Error: {error}",
        "searching": "🔍 Searching for academic papers...",

        # API status messages
        "api_openai": "✅ OpenAI",
        "api_anthropic": "✅ Anthropic",
        "api_semantic_scholar_pro": "✅ Semantic Scholar (Pro)",
        "api_semantic_scholar_free": "✅ Semantic Scholar (Free)",

        # Footer
        "footer": "AI Academic Paper Assistant • Zero Hallucination Guarantee • Built with ❤️ using Streamlit, Semantic Scholar, and LLMs",

        # Language selection
        "language": "Language",
        "language_en": "English",
        "language_zh": "中文",

        # Config management
        "config_reload": "Reload",

        # Network status
        "network_status": "🌐 Network Status",
        "network_check": "Check Connection",
        "network_checking": "Checking connection...",

        # Cross-paper analysis
        "cross_paper_analysis_title": "📊 Cross-Paper Analysis",
        "cross_paper_individual_title": "Individual Paper Analysis",
        "paper_analysis_keywords": "Keywords",
        "paper_analysis_method": "Research Method",
        "paper_analysis_contributions": "Main Contributions",
        "paper_analysis_limitations": "Limitations",
        "cross_paper_individual_hint": "Click to view detailed analysis of individual papers",

        # Stats bar
        "stats_total_papers": "Papers Found",
        "stats_total_citations": "Total Citations",
        "stats_avg_citations": "Avg Citations",
        "stats_date_range": "Date Range",

        # Sidebar sections
        "sidebar_config_info": "Configuration",
        "sidebar_api_section": "API Status",

        # Cross-paper analysis
        "cross_paper_key_findings_list": "Key Findings",

        # Follow-up questions
        "followup_title": "Ask Follow-up Questions",
        "followup_input_label": "Enter your question:",
        "followup_input_placeholder": "e.g., 'Tell me more about paper [1]', 'Find similar papers'",
        "followup_button": "Ask",
        "followup_processing": "Processing your question...",
        "followup_question": "Question",
    },

    "zh": {
        # App titles and headers
        "app_title": "📚 AI 学术论文助手",
        "app_subtitle": "搜索学术论文并获得零幻觉的AI驱动摘要",
        "last_search": "上次搜索：'{query}'",

        # Sidebar
        "sidebar_config_auto": "配置优先从 .env 加载；若无则读取 config/config.json；点击「重新加载」刷新。",
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
        "search_empty_query": "请先输入检索内容，再点击搜索。",

        # Results
        "results_found": "找到 {count} 篇相关论文",
        "results_answer": "🤖 AI 驱动答案",
        "results_references": "📚 参考文献",

        # Paper card
        "paper_year": "年份",
        "paper_citations": "引用",
        "paper_reference_count": "参考文献",
        "paper_abstract": "摘要",
        "paper_read_more": "阅读论文",
        "paper_venue": "发表刊物",
        "paper_fields_of_study": "研究领域",
        "paper_cited_in_answer": "答案引用",

        # Warnings and errors
        "warning_no_llm_keys": "⚠️ 未检测到 LLM API 密钥。请在 .env 文件中设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 以启用 AI 驱动的答案。Semantic Scholar 搜索仍可工作。",
        "error_search": "错误：{error}",
        "searching": "🔍 正在搜索学术论文...",

        # API status messages
        "api_openai": "✅ OpenAI",
        "api_anthropic": "✅ Anthropic",
        "api_semantic_scholar_pro": "✅ Semantic Scholar (Pro)",
        "api_semantic_scholar_free": "✅ Semantic Scholar (Free)",

        # Footer
        "footer": "AI 学术论文助手 • 零幻觉保证 • 使用 Streamlit、Semantic Scholar 和 LLMs 构建，用心打造 ❤️",

        # Language selection
        "language": "语言",
        "language_en": "English",
        "language_zh": "中文",

        # Config management
        "config_reload": "重新加载",

        # Network status
        "network_status": "🌐 网络状态",
        "network_check": "检查连接",
        "network_checking": "检查连接状态...",

        # Cross-paper analysis
        "cross_paper_analysis_title": "📊 跨论文综合分析",
        "cross_paper_individual_title": "单篇论文分析",
        "paper_analysis_keywords": "关键词",
        "paper_analysis_method": "研究方法",
        "paper_analysis_contributions": "主要贡献",
        "paper_analysis_limitations": "局限性",
        "cross_paper_individual_hint": "点击查看单篇论文的详细分析",

        # Stats bar
        "stats_total_papers": "检索论文",
        "stats_total_citations": "总引用数",
        "stats_avg_citations": "平均引用",
        "stats_date_range": "时间跨度",

        # Sidebar sections
        "sidebar_config_info": "配置信息",
        "sidebar_api_section": "API接口状态",

        # Cross-paper analysis
        "cross_paper_key_findings_list": "关键发现",

        # Follow-up questions
        "followup_title": "追问研究助手",
        "followup_input_label": "输入你的问题：",
        "followup_input_placeholder": "例如：'深入分析论文[1]', '找到类似论文'",
        "followup_button": "提问",
        "followup_processing": "正在处理你的问题...",
        "followup_question": "问题",
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
