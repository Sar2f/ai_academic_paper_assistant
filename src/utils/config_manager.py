import os
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import asdict
from .config import AppConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """Configuration manager supporting multiple persistence options."""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Optional custom configuration directory
        """
        self.config_dir = config_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config"
        )
        os.makedirs(self.config_dir, exist_ok=True)

        # Configuration file paths
        self.env_file = ".env"
        self.json_file = os.path.join(self.config_dir, "config.json")
        self.current_source = None
        self.current_config = None

    def detect_config_source(self) -> str:
        """
        Detect which configuration source is available.

        Returns:
            "env" if .env file exists, "json" if config.json exists, "default" otherwise
        """
        if os.path.exists(self.env_file):
            logger.info(f"Found environment file: {self.env_file}")
            return "env"
        elif os.path.exists(self.json_file):
            logger.info(f"Found JSON config file: {self.json_file}")
            return "json"
        else:
            logger.info("No config file found, using default configuration")
            return "default"

    def load_config(self, source: Optional[str] = None) -> AppConfig:
        """
        Load configuration from the specified source.

        Args:
            source: "env", "json", or None for auto-detection

        Returns:
            AppConfig instance
        """
        if source is None:
            source = self.detect_config_source()

        self.current_source = source

        if source == "env":
            config = self._load_from_env()
        elif source == "json":
            config = self._load_from_json()
        else:  # default
            config = AppConfig()

        # Validate configuration
        try:
            config.validate()
            logger.info(f"Configuration loaded successfully from {source}")
        except ValueError as e:
            logger.warning(f"Configuration validation failed: {e}")
            # Still return the config, but log the warning

        self.current_config = config
        return config

    def _load_from_env(self) -> AppConfig:
        """Load configuration from environment variables."""
        return AppConfig.from_env()

    def _load_from_json(self) -> AppConfig:
        """Load configuration from JSON file."""
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert JSON data to AppConfig
            return AppConfig(
                openai_api_key=data.get("openai_api_key"),
                anthropic_api_key=data.get("anthropic_api_key"),
                semantic_scholar_api_key=data.get("semantic_scholar_api_key"),
                max_papers_to_retrieve=data.get("max_papers_to_retrieve", 10),
                api_base_url=data.get("api_base_url"),
                llm_model=data.get("llm_model", "gpt-4o-mini"),
                max_tokens=data.get("max_tokens", 2000),
                temperature=data.get("temperature", 0.1),
                rate_limit_delay=data.get("rate_limit_delay", 0.1),
                use_mock_data=data.get("use_mock_data", False),
                streamlit_port=data.get("streamlit_port", 8501),
                streamlit_host=data.get("streamlit_host", "0.0.0.0"),
            )
        except FileNotFoundError:
            logger.warning(f"JSON config file not found: {self.json_file}")
            return AppConfig()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return AppConfig()

    def save_config(self, config: AppConfig, source: str) -> bool:
        """
        Save configuration to the specified source.

        Args:
            config: AppConfig instance
            source: "env" or "json"

        Returns:
            True if successful, False otherwise
        """
        try:
            if source == "env":
                return self._save_to_env(config)
            elif source == "json":
                return self._save_to_json(config)
            else:
                logger.error(f"Unsupported config source: {source}")
                return False
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def _save_to_env(self, config: AppConfig) -> bool:
        """Save configuration to .env file."""
        try:
            lines = []
            lines.append("# OpenAI API Key")
            lines.append(f"OPENAI_API_KEY={config.openai_api_key or ''}")
            lines.append("")
            lines.append("# Third-party API Base URL (OpenAI-compatible)")
            lines.append(f"API_BASE_URL={config.api_base_url or ''}")
            lines.append("")
            lines.append("# Anthropic API Key")
            lines.append(f"ANTHROPIC_API_KEY={config.anthropic_api_key or ''}")
            lines.append("")
            lines.append("# Semantic Scholar API Key")
            lines.append(
                f"SEMANTIC_SCHOLAR_API_KEY={config.semantic_scholar_api_key or ''}"
            )
            lines.append("")
            lines.append("# Application Settings")
            lines.append(f"MAX_PAPERS_TO_RETRIEVE={config.max_papers_to_retrieve}")
            lines.append(f"LLM_MODEL={config.llm_model}")
            lines.append(f"MAX_TOKENS={config.max_tokens}")
            lines.append(f"TEMPERATURE={config.temperature}")
            lines.append(f"RATE_LIMIT_DELAY={config.rate_limit_delay}")
            lines.append(f"USE_MOCK_DATA={'true' if config.use_mock_data else 'false'}")
            lines.append(f"STREAMLIT_PORT={config.streamlit_port}")
            lines.append(f"STREAMLIT_HOST={config.streamlit_host}")
            lines.append("")

            with open(self.env_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            logger.info(f"Configuration saved to env file: {self.env_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save env config: {e}")
            return False

    def _save_to_json(self, config: AppConfig) -> bool:
        """Save configuration to JSON file."""
        try:
            config_dict = asdict(config)

            # Remove None values for cleaner JSON
            config_dict = {k: v for k, v in config_dict.items() if v is not None}

            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to JSON file: {self.json_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON config: {e}")
            return False

    def create_config_template(self, source: str) -> bool:
        """
        Create a configuration template file.

        Args:
            source: "env" or "json"

        Returns:
            True if successful, False otherwise
        """
        if source == "env":
            # Create from .env.example
            env_example = os.path.join(os.path.dirname(self.env_file), ".env.example")
            if os.path.exists(env_example):
                try:
                    with open(env_example, "r", encoding="utf-8") as src:
                        with open(self.env_file, "w", encoding="utf-8") as dst:
                            dst.write(src.read())
                    logger.info(f"Created .env file from template: {self.env_file}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to create .env file: {e}")
                    return False
            else:
                logger.error(f".env.example not found: {env_example}")
                return False
        elif source == "json":
            # Create empty JSON template
            template = {
                "openai_api_key": None,
                "anthropic_api_key": None,
                "semantic_scholar_api_key": None,
                "max_papers_to_retrieve": 10,
                "api_base_url": None,
                "llm_model": "gpt-4o-mini",
                "max_tokens": 2000,
                "temperature": 0.1,
                "rate_limit_delay": 0.1,
                "use_mock_data": False,
                "streamlit_port": 8501,
                "streamlit_host": "0.0.0.0",
            }

            try:
                with open(self.json_file, "w", encoding="utf-8") as f:
                    json.dump(template, f, indent=2, ensure_ascii=False)
                logger.info(f"Created JSON config template: {self.json_file}")
                return True
            except Exception as e:
                logger.error(f"Failed to create JSON config template: {e}")
                return False
        else:
            logger.error(f"Unsupported config source: {source}")
            return False

    def get_config_info(self) -> Dict[str, Any]:
        """
        Get information about current configuration.

        Returns:
            Dictionary with config information
        """
        info = {
            "current_source": self.current_source,
            "config_dir": self.config_dir,
            "env_file_exists": os.path.exists(self.env_file),
            "json_file_exists": os.path.exists(self.json_file),
            "env_example_exists": os.path.exists(".env.example"),
        }

        if self.current_config:
            config_dict = asdict(self.current_config)
            # Hide API keys for security
            for key in [
                "openai_api_key",
                "anthropic_api_key",
                "semantic_scholar_api_key",
            ]:
                if config_dict.get(key):
                    config_dict[key] = "***HIDDEN***"
            info["current_config"] = config_dict

        return info
