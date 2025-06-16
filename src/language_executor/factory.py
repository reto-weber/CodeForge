from typing import Dict, Type
from .base import LanguageExecutor
from .python_executor import PythonExecutor
from .c_executor import CExecutor
from .cpp_executor import CppExecutor
from .java_executor import JavaExecutor
from .eiffel_executor import EiffelExecutor
from config_manager import get_config_manager


# Mapping of executor class names to actual classes
_EXECUTOR_CLASSES: Dict[str, Type[LanguageExecutor]] = {
    "PythonExecutor": PythonExecutor,
    "CExecutor": CExecutor,
    "CppExecutor": CppExecutor,
    "JavaExecutor": JavaExecutor,
    "EiffelExecutor": EiffelExecutor,
}


def _build_language_executor_map() -> Dict[str, Type[LanguageExecutor]]:
    """Build the language executor map from configuration."""
    config = get_config_manager()
    executor_map = {}

    for lang_id in config.get_supported_languages():
        try:
            # Get the executor class name from config
            executor_class_name = config.get_executor_class_name(lang_id)
            if not executor_class_name:
                print(
                    f"Warning: No executor class configured for "
                    f"language '{lang_id}'"
                )
                continue

            # Get the actual executor class
            executor_class = _EXECUTOR_CLASSES.get(executor_class_name)
            if executor_class is None:
                print(
                    f"Warning: Unknown executor class '{executor_class_name}' "
                    f"for language '{lang_id}'"
                )
                continue

            executor_map[lang_id] = executor_class

        except ValueError as e:
            print(f"Warning: Error setting up executor for language '{lang_id}': {e}")
            continue

    return executor_map


# Build the executor map from configuration
_LANGUAGE_EXECUTOR_MAP = _build_language_executor_map()


def get_supported_languages() -> list[str]:
    """Get list of supported languages."""
    return list(_LANGUAGE_EXECUTOR_MAP.keys())


def is_language_supported(language: str) -> bool:
    """Check if a language is supported."""
    return language in _LANGUAGE_EXECUTOR_MAP


def get_executor_by_name(
    language_name: str, version: str | None = None
) -> LanguageExecutor:
    """Get executor by language name string."""
    if not is_language_supported(language_name):
        raise ValueError(f"Unsupported language: {language_name}")

    executor_class = _LANGUAGE_EXECUTOR_MAP[language_name]
    return executor_class(version)


def reload_executors():
    """Reload executor map from configuration (useful for dynamic config changes)."""
    global _LANGUAGE_EXECUTOR_MAP
    get_config_manager().reload_config()
    _LANGUAGE_EXECUTOR_MAP = _build_language_executor_map()
