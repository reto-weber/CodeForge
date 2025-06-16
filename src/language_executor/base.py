from abc import ABC, abstractmethod
from typing import Tuple, Optional


class LanguageExecutor(ABC):
    """
    Abstract base class for language execution and compilation.
    """

    def __init__(self, version: Optional[str] = None):
        self.version = version

    @abstractmethod
    def compile(self, code: str, session_id: str) -> Tuple[bool, str, Optional[str]]:
        """
        Compile the code. Returns (success, output, output_path).
        """
        pass

    @abstractmethod
    def execute(
        self, code: str, session_id: str, timeout: int = 30
    ) -> Tuple[bool, str, int]:
        """
        Execute the code. Returns (success, output, exit_code).
        """
        pass
