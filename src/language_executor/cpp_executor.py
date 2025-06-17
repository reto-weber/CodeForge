from .base import LanguageExecutor, FileInfo
from typing import Tuple, Optional, Union, List
from container_manager import get_container_manager


class CppExecutor(LanguageExecutor):
    def _normalize_input(
        self, code: Union[str, List[FileInfo]], main_file: Optional[str] = None
    ) -> Tuple[List[FileInfo], str]:
        """
        Convert input to normalized format for C++.
        Ensures single-file mode creates a .cpp file.
        """
        if isinstance(code, str):
            # Legacy single-file mode - ensure .cpp extension
            filename = main_file or "main.cpp"
            if not filename.endswith(".cpp"):
                if "." in filename:
                    filename = filename.rsplit(".", 1)[0] + ".cpp"
                else:
                    filename = filename + ".cpp"
            return [FileInfo(filename, code)], filename
        else:
            # Multi-file mode
            files = code
            if main_file:
                return files, main_file
            else:
                # If no main file specified, use the first .cpp file or first file
                cpp_files = [f for f in files if f.name.endswith(".cpp")]
                if cpp_files:
                    main_filename = cpp_files[0].name
                elif files:
                    main_filename = files[0].name
                else:
                    main_filename = "main.cpp"
                return files, main_filename

    def compile(
        self,
        code: Union[str, List[FileInfo]],
        session_id: str,
        main_file: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        container_mgr = get_container_manager()

        if not container_mgr.create_session_container(session_id, "cpp"):
            return False, "Failed to create compilation container", None

        # Handle both legacy string and new multi-file formats
        files, _ = self._normalize_input(code, main_file)

        # Write all files to container
        if not self._write_files_to_container(files, session_id):
            return False, "Failed to copy files to container", None

        # For C++, compile all .cpp files together
        cpp_files = [f.name for f in files if f.name.endswith(".cpp")]
        if not cpp_files:
            return False, "No C++ source files found", None

        cmd = f"g++ {' '.join(cpp_files)} -o code.out"
        exec_result = container_mgr.run_command_in_container(session_id, cmd, 30)
        if exec_result is None:
            return False, "Failed to compile code in container", None

        stdout = exec_result.output[0].decode("utf-8") if exec_result.output[0] else ""
        stderr = exec_result.output[1].decode("utf-8") if exec_result.output[1] else ""
        exit_code = exec_result.exit_code
        output = stdout if exit_code == 0 else (stderr or stdout)
        success = exit_code == 0
        output_path = "code.out" if success else None
        return success, output, output_path

    def execute(
        self,
        code: Union[str, List[FileInfo]],
        session_id: str,
        timeout: int = 30,
        main_file: Optional[str] = None,
    ) -> Tuple[bool, str, int]:
        container_mgr = get_container_manager()

        # For multi-file execution, write files if needed
        if isinstance(code, list):
            if not self._write_files_to_container(code, session_id):
                return False, "Failed to copy files to container", -1

        run_cmd = "./code.out"
        run_result = container_mgr.run_command_in_container(
            session_id, run_cmd, timeout
        )
        if run_result is None:
            return False, "Failed to execute binary in container", -1

        stdout = run_result.output[0].decode("utf-8") if run_result.output[0] else ""
        stderr = run_result.output[1].decode("utf-8") if run_result.output[1] else ""
        exit_code = run_result.exit_code
        output = stdout if exit_code == 0 else (stderr or stdout)
        success = exit_code == 0
        return success, output, exit_code
