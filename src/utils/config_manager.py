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
        self.config_dir = config_dir or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

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
            logger.info("Found environment file: %s", self.env_file)
            return "env"
        if os.path.exists(self.json_file):
            logger.info("Found JSON config file: %s", self.json_file)
            return "json"
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
            logger.info("Configuration loaded successfully from %s", source)
        except ValueError as e:
            logger.warning("Configuration validation failed: %s", e)
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
                semantic_scholar_api_key=data.get("semantic_scholar_api_key"),
                max_papers_to_retrieve=data.get("max_papers_to_retrieve", 10),
                api_base_url=data.get("api_base_url"),
                llm_model=data.get("llm_model", "gpt-4o-mini"),
                max_tokens=data.get("max_tokens", 2000),
                temperature=data.get("temperature", 0.1),
                rate_limit_delay=data.get("rate_limit_delay", 0.1),
                streamlit_port=data.get("streamlit_port", 8501),
                streamlit_host=data.get("streamlit_host", "0.0.0.0"),
            )
        except FileNotFoundError:
            logger.warning("JSON config file not found: %s", self.json_file)
            return AppConfig()
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in config file: %s", e)
            return AppConfig()


