from typing import Optional, Tuple

from container_manager import get_container_manager

from .base import LanguageExecutor


class PythonExecutor(LanguageExecutor):
    def compile(self, code: str, session_id: str) -> Tuple[bool, str, Optional[str]]:
        # Python does not need compilation
        return True, "No compilation needed for Python", None

    def execute(
        self, code: str, session_id: str, timeout: int = 30
    ) -> Tuple[bool, str, int]:
        container_mgr = get_container_manager()
        filename = "code.py"
        # Ensure container exists
        if not container_mgr.create_session_container(session_id, "python"):
            return False, "Failed to create execution container", -1
        # Copy code file
        if not container_mgr.put_file_in_container(session_id, filename, code):
            return False, "Failed to copy code to container", -1
        # Run command
        cmd = f"python3 {filename}"
        exec_result = container_mgr.run_command_in_container(session_id, cmd, timeout)
        if exec_result is None:
            return False, "Failed to execute command in container", -1
        stdout = exec_result.output[0].decode("utf-8") if exec_result.output[0] else ""
        stderr = exec_result.output[1].decode("utf-8") if exec_result.output[1] else ""
        exit_code = exec_result.exit_code
        output = stdout if exit_code == 0 else (stderr or stdout)
        success = exit_code == 0
        return success, output, exit_code
