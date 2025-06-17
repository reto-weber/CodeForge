from abc import ABC, abstractmethod
from typing import Tuple, Optional, List, Union


class FileInfo:
    """Information about a source file."""

    def __init__(self, name: str, content: str):
        self.name = name
        self.content = content


class LanguageExecutor(ABC):
    """
    Abstract base class for language execution and compilation.
    """

    def __init__(self, version: Optional[str] = None):
        self.version = version

    @abstractmethod
    def compile(
        self,
        code: Union[str, List[FileInfo]],
        session_id: str,
        main_file: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Compile the code.
        Args:
            code: Either a string (legacy) or list of FileInfo objects
            session_id: Session identifier
            main_file: Name of the main file (for multi-file projects)
        Returns: (success, output, output_path)
        """
        pass

    @abstractmethod
    def execute(
        self,
        code: Union[str, List[FileInfo]],
        session_id: str,
        timeout: int = 30,
        main_file: Optional[str] = None,
    ) -> Tuple[bool, str, int]:
        """
        Execute the code.
        Args:
            code: Either a string (legacy) or list of FileInfo objects
            session_id: Session identifier
            timeout: Execution timeout
            main_file: Name of the main file (for multi-file projects)
        Returns: (success, output, exit_code)
        """
        pass

    def _write_files_to_container(self, files: List[FileInfo], session_id: str) -> bool:
        """
        Helper method to write multiple files to the container.
        Returns True if all files were written successfully.
        """
        from container_manager import get_container_manager

        container_mgr = get_container_manager()

        for file_info in files:
            if not container_mgr.put_file_in_container(
                session_id, file_info.name, file_info.content
            ):
                return False
        return True

    def _normalize_input(
        self, code: Union[str, List[FileInfo]], main_file: Optional[str] = None
    ) -> Tuple[List[FileInfo], str]:
        """
        Convert input to normalized format.
        Returns (files_list, main_file_name)
        """
        if isinstance(code, str):
            # Legacy single-file mode
            filename = main_file or "code.txt"  # Default filename
            return [FileInfo(filename, code)], filename
        else:
            # Multi-file mode
            files = code
            if main_file:
                return files, main_file
            else:
                # If no main file specified, use the first file
                return files, files[0].name if files else "code.txt"
