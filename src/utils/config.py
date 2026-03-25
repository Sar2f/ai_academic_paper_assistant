import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration."""
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    semantic_scholar_api_key: Optional[str] = None
    
    # Application Settings
    max_papers_to_retrieve: int = 10
    llm_model: str = "gpt-4o"
    max_tokens: int = 2000
    temperature: float = 0.1
    rate_limit_delay: float = 0.1
    use_mock_data: bool = True  # Use mock data for demonstration
    
    # UI Settings
    streamlit_port: int = 8501
    streamlit_host: str = "0.0.0.0"
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables."""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            semantic_scholar_api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY"),
            max_papers_to_retrieve=int(os.getenv("MAX_PAPERS_TO_RETRIEVE", "10")),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o"),
            max_tokens=int(os.getenv("MAX_TOKENS", "2000")),
            temperature=float(os.getenv("TEMPERATURE", "0.1")),
            rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", "0.1")),
            use_mock_data=os.getenv("USE_MOCK_DATA", "true").lower() == "true",
            streamlit_port=int(os.getenv("STREAMLIT_PORT", "8501")),
            streamlit_host=os.getenv("STREAMLIT_HOST", "0.0.0.0")
        )
    
    def validate(self) -> bool:
        """Validate configuration."""
        errors = []
        
        # Check if at least one LLM API key is set
        if not self.openai_api_key and not self.anthropic_api_key:
            errors.append("必须设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY")
        
        # Validate LLM model choice
        if self.llm_model.startswith("gpt-") and not self.openai_api_key:
            errors.append(f"模型 {self.llm_model} 需要 OPENAI_API_KEY")
        elif self.llm_model.startswith("claude-") and not self.anthropic_api_key:
            errors.append(f"模型 {self.llm_model} 需要 ANTHROPIC_API_KEY")
        
        # Validate numeric ranges
        if self.max_papers_to_retrieve < 1 or self.max_papers_to_retrieve > 50:
            errors.append("MAX_PAPERS_TO_RETRIEVE 必须在 1 到 50 之间")
        
        if self.max_tokens < 100 or self.max_tokens > 4000:
            errors.append("MAX_TOKENS 必须在 100 到 4000 之间")
        
        if self.temperature < 0 or self.temperature > 1:
            errors.append("TEMPERATURE 必须在 0 到 1 之间")
        
        if errors:
            raise ValueError("配置错误：\n" + "\n".join(f"  - {error}" for error in errors))
        
        return True
    
    def get_available_models(self) -> list:
        """Get list of available LLM models based on API keys."""
        models = []
        
        if self.openai_api_key:
            models.extend(["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        
        if self.anthropic_api_key:
            models.extend(["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"])
        
        return models