"""
Configuration management for the code compiler application.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            # Default to the config directory relative to this file
            config_dir = Path(__file__).parent / "config"
        self.config_dir = Path(config_dir)
        self._languages_config: Optional[Dict[str, Any]] = None
        self._compiler_config: Optional[Dict[str, Any]] = None

    @property
    def languages_config(self) -> Dict[str, Any]:
        """Get the languages configuration."""
        if self._languages_config is None:
            self._load_languages_config()
        return self._languages_config or {}

    @property
    def compiler_config(self) -> Dict[str, Any]:
        """Get the compiler configuration."""
        if self._compiler_config is None:
            self._load_compiler_config()
        return self._compiler_config or {}

    def _load_languages_config(self):
        """Load the languages configuration from file."""
        config_path = self.config_dir / "languages.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._languages_config = json.load(f)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Languages config file not found: {config_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in languages config file: {exc}") from exc

    def _load_compiler_config(self):
        """Load the compiler configuration from file."""
        config_path = self.config_dir / "compiler_config.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._compiler_config = json.load(f)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Compiler config file not found: {config_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in compiler config file: {exc}") from exc

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language identifiers."""
        languages = self.languages_config.get("supported_languages", {})
        return [
            lang for lang, config in languages.items() if config.get("enabled", True)
        ]

    def get_language_config(self, language: str) -> Dict[str, Any]:
        """Get configuration for a specific language."""
        languages = self.languages_config.get("supported_languages", {})
        if language not in languages:
            raise ValueError(f"Unsupported language: {language}")
        return languages[language]

    def get_default_language(self) -> str:
        """Get the default language."""
        return self.languages_config.get("default_language", "python")

    def get_executor_class_name(self, language: str) -> Optional[str]:
        """Get the executor class name for a language."""
        lang_config = self.get_language_config(language)
        return lang_config.get("executor_class")

    def reload_config(self):
        """Reload configuration from files."""
        self._languages_config = None
        self._compiler_config = None


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_supported_languages() -> List[str]:
    """Get list of supported language identifiers."""
    config = get_config_manager()
    return config.get_supported_languages()
